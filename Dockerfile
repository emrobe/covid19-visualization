FROM continuumio/miniconda3

# General image set-up

ENV HOME /root
WORKDIR ${HOME}

RUN apt update && \
#RUN apt install -y curl build-essential
RUN conda config --add channels conda-forge
RUN conda config --add channels bioconda
#RUN conda create -n env python=3.7 htseq numpy pandas bokeh=1.2

COPY . covid19-visualization

RUN conda create --name env --file covid19-visualization/dependencies.txt
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

ENTRYPOINT ["bokeh", "serve", "covid19-visualization/"]
