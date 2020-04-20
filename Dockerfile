FROM continuumio/miniconda3

ENV HOME /root
WORKDIR ${HOME}
RUN git clone https://github.com/emrobe/covid19-visualization.git
RUN apt-get update
#RUN apt-get install -y curl build-essential
RUN conda config --add channels conda-forge
RUN conda config --add channels bioconda
#RUN conda create -n env python=3.7 htseq numpy pandas bokeh=1.2
RUN conda create --name env --file covid19-visualization/dependencies.txt
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH
#RUN python mmp_interactive/update_and_deploy_input_data.py
# Modify the EXPOSE and bokeh serve statement with --port and maybe --allow-websocket-origin to fit your needs.
EXPOSE 5006
CMD ["bokeh", "serve", "--port", "5006", "covid19vis/"]
