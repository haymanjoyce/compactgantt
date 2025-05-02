from models.time_frame import TimeFrame
from validators.validators import DataValidator

class TimeFrameService:
    def __init__(self):
        self.validator = DataValidator()

    def add_time_frame(self, project_data, time_frame_id, finish_date, width_proportion):
        time_frame = TimeFrame(time_frame_id, finish_date, width_proportion)
        used_ids = {tf.time_frame_id for tf in project_data.time_frames}
        errors = self.validator.validate_time_frame(time_frame, used_ids)
        if not errors:
            project_data.time_frames.append(time_frame)
            project_data.time_frames.sort(key=lambda x: x.time_frame_id)
        return errors

    # Add more time frame operations as needed
