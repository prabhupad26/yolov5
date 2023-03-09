import os
import requests

from utils.flask_rest_api.traffic_inspector.helper import initialize_vision_objects
from utils.flask_rest_api.traffic_inspector.helper import draw_boxes, save_with_bbox_renders
from PIL import Image


class TrafficInspector:
    def __init__(self, stl_list, exec_mode, ttl_simulation=60):
        self.stl_list = stl_list
        self.ttl_simulation = ttl_simulation
        self.final_dict = {i: {stl_list[0]['name']: {}, stl_list[1]['name']: {}} for i in range(ttl_simulation + 1)}
        self.active_count = 0
        self.inactive_count = 0
        self.priority_v_labels = ["ambulance", "police_car", "firetruck"]
        self.default_adjust = 5
        self.priority_adjust = 10
        self.priority_v_status = False
        self.stl_timer_default = 30
        self.exec_mode = exec_mode

    def run_simulation(self):
        if self.exec_mode == "image_mode":
            return self.process_image_mode()
        # initialization
        sim_counter = 0
        stl_timer_default = 30
        for stl in self.stl_list:
            stl['time_remaining'] = stl_timer_default
            stl['has_priority'] = False
            stl['skip_scene'] = 0
            stl['inactive_lane_glimpse'] = None
        # sim loop start
        while sim_counter <= self.ttl_simulation:
            print(f"sim_counter is : {sim_counter}")
            for stl in self.stl_list:
                self.update_results(sim_counter, stl)
                if stl['status'] == 'green':
                    traffic_details, _ = next(stl['vision_iter'])
                    self.active_count = len(traffic_details.values())
                    stl['has_priority'] = self.has_priority_vehicle(stl['name'],
                                                                    traffic_details)
                    print(f"{stl['name']} has {self.active_count} vehicles")
                else:
                    if stl['inactive_lane_glimpse'] is None:
                        traffic_details, _ = next(stl['vision_iter'])
                        stl['inactive_lane_glimpse'] = traffic_details
                    stl['has_priority'] = self.has_priority_vehicle(stl['name'],
                                                                    stl['inactive_lane_glimpse'])

                    skip_scene = 65 if (sim_counter == 30 and stl['status'] == 'red') else 0
                    if skip_scene:
                        self.inactive_count = self.get_traffic_count(iter_=stl['vision_iter'],
                                                                     skip_scene=skip_scene)
                    else:
                        self.inactive_count = len(stl['inactive_lane_glimpse'].values())
                    stl['skip_scene'] = skip_scene
                    print(f"{stl['name']} has {self.inactive_count} vehicles")

            if stl_timer_default <= 0:
                stl_timer_default = self.stl_timer_default

            if self.active_count < self.inactive_count:
                if self.default_adjust > stl_timer_default:
                    stl_timer_default = stl_timer_default - self.default_adjust
                self.toggle_status()
            else:
                stl_timer_default -= 1

            for stl in self.stl_list:
                if stl['has_priority'] and self.priority_adjust < stl_timer_default and stl['status'] != 'green':
                    stl_timer_default = stl_timer_default - self.priority_adjust
                stl['time_remaining'] = stl_timer_default

            sim_counter += 1
        return self.final_dict

    def process_image_mode(self):
        input_data_path = "static\\videos\\scenario_1_image_mode"
        input_data_path = os.path.join(os.getcwd(), input_data_path)
        lane1_img = "lane_1_feed_user1.jpg"
        lane2_img = "lane_2_feed_user1.jpg"
        lane2img_map = {"lane1": {"img_name": lane1_img,
                                  "tl_status": None},
                        "lane2": {"img_name": lane2_img,
                                  "tl_status": None}}
        result_dict = {}
        for img in [lane1_img, lane2_img]:
            result_dict[img] = {'vehicle_count': 0, 'priority_vehicle_count': 0}
            img_full_path = os.path.join(input_data_path, img)
            newly_rendered_image = Image.open(img_full_path)
            response = requests.post(f'http://127.0.0.1:5000/process_image',
                                    data=img_full_path)
            for prediction in response.json():
                result_dict[img]['vehicle_count'] += 1
                if prediction['class'] in self.priority_v_labels:
                    result_dict[img]['priority_vehicle_count'] += 1
                x0 = prediction['x'] - prediction['width'] / 2
                x1 = prediction['x'] + prediction['width'] / 2
                y0 = prediction['y'] - prediction['height'] / 2
                y1 = prediction['y'] + prediction['height'] / 2
                box = (x0, y0, x1, y1)

                newly_rendered_image = draw_boxes(box, x0, y0, newly_rendered_image, prediction['class'])
            save_with_bbox_renders(newly_rendered_image)
        lane1_count = result_dict[lane2img_map["lane1"]["img_name"]]['vehicle_count']
        lane2_count = result_dict[lane2img_map["lane2"]["img_name"]]["vehicle_count"]
        lane1_priority_count = result_dict[lane2img_map["lane1"]["img_name"]]['priority_vehicle_count']
        lane2_priority_count = result_dict[lane2img_map["lane2"]["img_name"]]['priority_vehicle_count']

        # logic for traffic management
        if lane1_count > lane2_count:
            lane2img_map["lane1"]["tl_status"] = "green"
            lane2img_map["lane2"]["tl_status"] = "red"
        else:
            lane2img_map["lane1"]["tl_status"] = "red"
            lane2img_map["lane2"]["tl_status"] = "green"

        if lane1_priority_count > lane2_priority_count:
            lane2img_map["lane1"]["tl_status"] = "green"
            lane2img_map["lane2"]["tl_status"] = "red"
        if lane1_priority_count < lane2_priority_count:
            lane2img_map["lane1"]["tl_status"] = "red"
            lane2img_map["lane2"]["tl_status"] = "green"
        return lane2img_map




    def scheduled_version(self):
        stl_timer_default = self.stl_timer_default
        for i in range(self.ttl_simulation):
            for stl in self.stl_list:
                stl['time_remaining'] = stl_timer_default
                stl['has_priority'] = False
                stl['skip_scene'] = 0
                self.update_results(i, stl)
            if stl_timer_default <= 0:
                stl_timer_default = self.stl_timer_default
                self.toggle_status()
            stl_timer_default -= 1
        return self.final_dict

    def toggle_status(self):
        for stl in self.stl_list:
            if stl['status'] == 'green':
                stl['status'] = 'red'
            else:
                stl['status'] = 'green'

    def update_results(self, sim_counter, stl_dict):
        self.final_dict[sim_counter][stl_dict['name']] = {
            "status": stl_dict['status'],
            "time_remaining": stl_dict['time_remaining'],
            "has_priority": stl_dict['has_priority'],
            "skip_scene": stl_dict['skip_scene']}

    def get_traffic_count(self, iter_=None, skip_scene=0):
        if skip_scene > 0 and iter_:
            traffic_details, _ = [next(iter_) for _ in range(skip_scene)][-1]
            return len(traffic_details.values())

    def has_priority_vehicle(self, stl_name, traffic_details):
        for label in self.priority_v_labels:
            if label in traffic_details.keys():
                print(f"{stl_name} has a priority vehicle {label}")
                return True
        return False


if __name__ == '__main__':
    vision_list = initialize_vision_objects('yolov5')
    stl_1_dict = {'name': 'stl_1', 'status': 'green', 'vision_iter': vision_list[0]}
    stl_2_dict = {'name': 'stl_2', 'status': 'red', 'vision_iter': vision_list[1]}
    ti_obj = TrafficInspector([stl_1_dict, stl_2_dict], 'video_mode')
    ti_obj.run_simulation()
