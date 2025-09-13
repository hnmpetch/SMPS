from utils.log import log



def create_dir():
    
    import os
    list_dir = [
        "backup",
        "model",
        "park_lot",
        "reports"
    ]
    
    for dir in list_dir:
        os.makedirs(dir, exist_ok=True)
        log.success_event(f"Success create directory: {dir}")
    