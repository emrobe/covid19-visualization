FROM continuumio/miniconda3

# General image set-up

ENV HOME /root
WORKDIR ${HOME}

#RUN apt update && \
#apt install -y curl build-essential
RUN conda config --add channels conda-forge && \
  conda config --add channels bioconda
#RUN conda create -n env python=3.7 htseq numpy pandas bokeh=1.2
ENV PATH /opt/conda/envs/env/bin:$PATH

COPY dependencies.txt /tmp/dependencies.txt
RUN conda create --name env --file /tmp/dependencies.txt && \
  rm /tmp/dependencies.txt && \
  echo "source activate env" > ~/.bashrc

COPY . covid19-visualization

ENTRYPOINT ["bokeh", "serve", "covid19-visualization/"]
