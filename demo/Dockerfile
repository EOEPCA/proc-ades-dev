FROM ades:latest

WORKDIR /workspace
RUN pip install jupyter -U && pip install jupyterlab
EXPOSE 8888

CMD ["sh" , "-c", "jupyter lab --notebook-dir=/notebooks --ip=0.0.0.0 --allow-root & apachectl -D FOREGROUND"]


