CONFIGS = {
    "estudiante": 2,
    "session": "1",
    "store_location": ".",
    "folder": "Estudiante_1",
    "video": True,
    "audio": False,
    "mqtt_hostname": "200.126.23.131",
    "mqtt_username" : "james",
    "mqtt_password" : "james",
    "mqtt_port" : 1883,
    "dev_id": "1"
}

CONFIGS['video_folder'] = CONFIGS['store_location'] + "/videos_{}/"
CONFIGS['audio_folder'] = CONFIGS['store_location'] + "/session_{}/"+CONFIGS['folder']+"/Audio/"

CAMERA = {
    "brightness": 60,
    "saturation": -60,
    "contrast" : 0,
    # "resolution": (1280,720),
    "resolution": (1296,972),
    "framerate": 5
}
