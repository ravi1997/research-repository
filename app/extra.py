
# EXTRA
def job_listener(event):
    if event.exception:
        print(f"The job with id {event.job_id} crashed at {event.scheduled_run_time}")
    else:
        print(f"The job with id {event.job_id} executed correctly at {event.scheduled_run_time}")
