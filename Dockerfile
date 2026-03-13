FROM registry.redhat.io/ubi10/python-312-minimal:10.1

WORKDIR /opt/app-root/src

COPY pyproject.toml .
COPY function/ function/
RUN pip install --no-cache-dir func-python==0.7.0 httpx .

RUN echo 'from func_python.http import serve; from function import new; serve(new)' > main.py

EXPOSE 8080
CMD ["python", "main.py"]
