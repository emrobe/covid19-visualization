# covid19-visualization

Visualization webapp for the Corona Portal

## Usage

The Docker image is automatically built after each commit.  
**Note:** The version is defined in [.gitlab-ci.yml](.gitlab-ci.yml).

To run the container:  
```
docker pull registry.gitlab.com/uit-sfb/covid19-visualization/covid19-visualization:<version> && \
docker run -p 5006:5006 registry.gitlab.com/uit-sfb/covid19-visualization/covid19-visualization:<version> [options]
```

To access the UI, open the following URL in your web browser:  
`http://localhost:5006`
