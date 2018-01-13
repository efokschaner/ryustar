FROM python:2.7.14
ADD locust-tasks /locust-tasks
RUN pip install -r /locust-tasks/requirements.txt
EXPOSE 5557 5558 8089
RUN chmod 755 /locust-tasks/run.sh

# Start Locust using LOCUS_OPTS environment variable
ENTRYPOINT ["/locust-tasks/run.sh"]
