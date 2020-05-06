FROM continuumio/miniconda3

ENV HOME /root
WORKDIR ${HOME}

RUN conda config --add channels conda-forge && \
  conda config --add channels bioconda
ENV PATH /opt/conda/envs/env/bin:$PATH

COPY dependencies.txt /tmp/dependencies.txt
RUN conda create --name env --file /tmp/dependencies.txt && \
  rm /tmp/dependencies.txt && \
  echo "source activate env" > ~/.bashrc

COPY . covid19-visualization

ENTRYPOINT ["bokeh", "serve", "covid19-visualization/"]
