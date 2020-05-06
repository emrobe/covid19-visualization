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

COPY . covid19-visualization

RUN conda create --name env --file covid19-visualization/dependencies.txt && \
  echo "source activate env" > ~/.bashrc

ENTRYPOINT ["bokeh", "serve", "covid19-visualization/"]
