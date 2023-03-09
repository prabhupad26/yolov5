import json
import os
import time
from typing import List, AnyStr, ByteString
import sys

import cv2
import requests


class Lane:
    def __init__(self, number: int, status: AnyStr = None, direction: AnyStr = None,
                 exit_lane: List = None, video_file: AnyStr = None, model_type: AnyStr=None) -> None:
        self.number = number
        self.status = status
        self.direction = direction
        self.exit_lane = exit_lane
        self.video = cv2.VideoCapture(video_file)
        self.model_type = model_type

    def get_frame(self, width: int = 640, height: int = 640) -> ByteString | None:
        """
        This generator will generate the bytestream object frame by frame
        :param width:
        :param height:
        :return:
        """
        current_time = 0
        interval = 1

        while self.video.isOpened():

            self.video.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)

            success, frame = self.video.read()
            if not success:
                self.video.release()
                return None
            _, buffer = cv2.imencode('.jpg', cv2.resize(frame, (width, height)))
            print(f"stl_{self.number} : At {current_time}:Sending video feed {sys.getsizeof(buffer.tobytes())} bytes ------> Flask inference api")
            yield buffer.tobytes()

            current_time += interval

        raise Exception(f"Unable to open video file for lane_{self.number}")

    def get_element_count(self) -> int:
        for frame in self.get_frame():
            response_json = requests.post(f'http://127.0.0.1:5000/v1/object-detection/{self.model_type}',
                                          data=frame)
            print(f"Response received for stl_{self.number}")
            traffic_details = {}
            response_json = response_json.json()

            for items in response_json:
                key_name = 'name' if 'name' in items else 'class'
                if items[key_name] not in traffic_details:
                    traffic_details[items[key_name]] = 0
                traffic_details[items[key_name]] += 1
            yield traffic_details, self.number

    def reset(self):
        self.video.release()


if __name__ == '__main__':
    input_data_path = "..\\static\\videos\\scenario_1"
    input_data_path = os.path.join(os.getcwd(), input_data_path)
    result = []
    with open(os.path.join(input_data_path, 'user1_inputs.json')) as cf:
        config_files = json.load(cf)
    stl_timer_default = int(config_files.get("initial_conditions").get("stl_timer_default"))

    # build lanes
    lanes = []
    lane_props_dict = config_files.get("initial_conditions").get("lane_props")
    if lane_props_dict:
        for lane_id, lane_props in lane_props_dict.items():
            if lane_props['video_feed']:
                video_path = os.path.join(input_data_path, lane_props['video_feed'])
            else:
                video_path = None
            lanes.append(Lane(int(lane_id), lane_props['status'], lane_props['lane_type']['direction'],
                              lane_props['lane_type']['exit'], video_path))
            # TODO : Build logic to support all scenarios
    else:
        print("No lanes configured by user")

    compare_lanes = [(lane, lane.get_element_count()) for lane in lanes if lane.number in [1, 2]]

    # start simulation
    sim_start_time = time.time()

    ln1_obj, ln1 = compare_lanes[0]
    ln2_obj, ln2 = compare_lanes[1]

    # initialize results dict
    results_dict = {}

    while time.time() - sim_start_time <= stl_timer_default:
        try:
            print("\033[96mTime elapsed : {:.02f}".format(time.time() - sim_start_time))
            traffic_details_1, num_1 = next(ln1)
            cnt_1 = sum(traffic_details_1.values())
            print(f"\033[91mVehicle count in lane_{num_1} is {cnt_1}")
            traffic_details_2, num_2 = next(ln2)
            cnt_2 = sum(traffic_details_2.values())
            print(f"\033[92mVehicle count in lane_{num_2} is {cnt_2}")

            # TODO : Traffic management logic goes in here
            _, lane_num = max((cnt_1, num_1), (cnt_2, num_2))

            results_dict[int(time.time() - sim_start_time)] = {f"lane_{lane_num}": True}

        except StopIteration:
            break

    ln1_obj.reset()
    ln2_obj.reset()

    print(f"results is {results_dict}")
