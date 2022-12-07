# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

FROM nvidia/cuda:11.3.0-cudnn8-runtime-ubuntu20.04 as build

ENV PYTHONUNBUFFERED TRUE

ARG tarball
ARG requirements
ARG my_secret
ARG model_store
ARG model_name

USER root

COPY dockerd-entrypoint.sh /usr/local/bin/dockerd-entrypoint.sh
RUN chmod +x /usr/local/bin/dockerd-entrypoint.sh

RUN mkdir -p /home/model-server/ \
    && mkdir -p /home/model-server/tmp \
    && mkdir -p /opt/ml/model/wikipedia-distillated

ENV TEMP=/home/model-server/tmp
ADD ${tarball} /home/model-server/runtime
COPY config.properties /home/model-server/runtime/

ENV DEBIAN_FRONTEND="noninteractive"
WORKDIR /tmp
ENV PIP_FIND_LINKS="file:///opt/lib/python" PIP_WHEEL_DIR="/opt/lib/python"
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       fakeroot \
       ca-certificates \
       dpkg-dev \
       g++ \
       python3.9 \
       python3.9-dev \
       python3.9-distutils \
       python-is-python3 \
       curl \
       vim \
       git \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p "/opt/lib/python" \
    && curl -O https://bootstrap.pypa.io/get-pip.py \
    && python3.9 get-pip.py \
    && chmod -R 550 /home/model-server/runtime/*


WORKDIR /home/model-server/code
# Install NLLB branch of fairseq, with GPU support
RUN /usr/local/bin/pip3 install --target /opt/lib/python/site-packages --no-cache-dir torch==1.12.1+cu113 torchaudio==0.12.1+cu113 torchserve -f https://download.pytorch.org/whl/torch_stable.html \
    && if [ ${requirements} = True ]; then /usr/local/bin/pip3 install --target /opt/lib/python/site-packages --no-cache-dir --force-reinstall -r /home/model-server/runtime/requirements.txt; fi \
    && git clone https://github.com/klausman/fairseq/ --branch wmfnllb --depth 5 fairseq_repo \
    && cd fairseq_repo && /usr/local/bin/pip3 install --target /opt/lib/python/site-packages --no-cache-dir '.[dev]'


FROM nvidia/cuda:11.3.0-cudnn8-runtime-ubuntu20.04 as production

USER root
RUN mkdir -p "/opt/lib/python" \
    && mkdir -p /home/model-server/logs \
    && chown 65534:65534 /home/model-server/logs \
    && mkdir -p /opt/ml/model/wikipedia-distillated \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
       python3.9 openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

COPY --chown=65534:65534 --from=build ["/opt/lib/python/site-packages", "/opt/lib/python/site-packages"]
COPY --chown=65534:65534 --from=build ["/usr/local/bin/dockerd-entrypoint.sh", "/usr/local/bin/dockerd-entrypoint.sh"]
COPY --chown=65534:65534 --from=build ["/home/model-server/runtime/", "/home/model-server/"]

USER 65534

WORKDIR /home/model-server
ENV PYTHONIOENCODING=UTF-8
ENV MODEL_STORE=${model_store}
ENV MODEL_NAME=${model_name}
ENV PATH="/opt/lib/python/site-packages/bin:${PATH}" PYTHONPATH="/opt/lib/python/site-packages"
ENTRYPOINT ["/usr/local/bin/dockerd-entrypoint.sh"]
CMD ["serve"]
