import os
import json

from PIL import Image, ImageDraw
from utils.flask_rest_api.traffic_inspector.infer_cv_api import Lane


def initialize_vision_objects(model_type):
    input_data_path = "static\\videos\\scenario_1"
    input_data_path = os.path.join(os.getcwd(), input_data_path)
    with open(os.path.join(input_data_path, 'user1_inputs.json')) as cf:
        config_files = json.load(cf)

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
                              lane_props['lane_type']['exit'], video_path, model_type))
            # TODO : Build logic to support all scenarios
    else:
        print("No lanes configured by user")

    compare_lanes = [lane.get_element_count() for lane in lanes if lane.number in [1, 2]]
    return compare_lanes


def draw_boxes(box, x0, y0, img, class_name):
    # OPTIONAL - color map, change the key-values for each color to make the
    # class output labels specific to your dataset
    color_map = {
        "car": "red",
        "ambulance": "blue",
        "transport_vehicle": "yellow",
        "firetruck": "green",
        "police_car": "black",
        "motorbike": "grey"
    }

    # get position coordinates
    bbox = ImageDraw.Draw(img)

    bbox.rectangle(box, outline=color_map[class_name], width=5)
    bbox.text((x0, y0), class_name, fill='black', anchor='mm')

    return img


def save_with_bbox_renders(img):
    output_data_path = "static\\videos\\scenario_1_image_mode\\output"
    output_data_path = os.path.join(os.getcwd(), output_data_path)
    file_name = os.path.basename(img.filename)
    img.save(os.path.join(output_data_path, file_name))
