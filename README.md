# Enhancing Open-Domain Task-Solving Capability of LLMs via Autonomous Tool Integration from GitHub

Code for paper "Enhancing Open-Domain Task-Solving Capability of LLMs via Autonomous Tool Integration from GitHub", presented at Proceedings of ACL 2025.

If you have any questions about this repo, please contact the author, Bohan Lyu, lyubh22@gmail.com.

## Abstract

Large Language Models (LLMs) excel in traditional natural language processing tasks but struggle with problems that require complex domain-specific calculations or simulations. While equipping LLMs with external tools to build LLM-based agents can enhance their capabilities, existing approaches lack the flexibility to address diverse and ever-evolving user queries in open domains. Currently, there is also no existing dataset that evaluates LLMs on open-domain knowledge that requires tools to solve. Notably, the largest open-domain platform is GitHub. To this end, we introduce **OpenAct** based on human expert consult and repositories in GitHub. It comprises 339 questions spanning 7 diverse domains that need to be solved with domain-specific methods. In our experiments, even state-of-the-art LLMs and LLM-based agents demonstrate shallow success rates on OpenAct, underscoring the need for a novel approach. Based on the characteristics of this task, we present **OpenAgent**, a novel LLM-based Agent system that can tackle evolving queries in open domains through autonomously integrating specialized tools from GitHub. OpenAgent employs (1) a hierarchical framework where specialized agents handle specific tasks and can assign tasks to inferior agents, (2) a bi-level experience learning mechanism to learn from both humans' and its own experiences to tackle tool flaws. Experiments demonstrate OpenAgent's superior effectiveness and efficiency that significantly outperforms current methods.

## Installation

To set up the environment, you'll need Python, Docker, a GitHub Token and the required dependencies. You can create the environment and install the required packages using the following commands:

```bash
conda create -n openact python=3.9.19
conda activate openact
pip install -r requirements.txt
docker build -t condaimage .
```

You should configure your GITHUB_TOKEN, OpenAI API, Model Name, and temperature in `config.json`. You can also use it to connect with your self-served local models.

The inputs of `Sniffles` are too large to upload, therefore you should download it them from the source:

```bash
cd src
HTTPDIR=https://storage.googleapis.com/deepvariant/case-study-testdata
curl ${HTTPDIR}/HG002.novaseq.pcr-free.35x.dedup.grch38_no_alt.chr20.bam > input/Sniffles/sample1/HG002.novaseq.pcr-free.35x.dedup.grch38_no_alt.chr20.bam
curl ${HTTPDIR}/HG002.novaseq.pcr-free.35x.dedup.grch38_no_alt.chr20.bam.bai > input/Sniffles/sample1/HG002.novaseq.pcr-free.35x.dedup.grch38_no_alt.chr20.bam.bai
HTTPDIR=https://storage.googleapis.com/deepvariant/pacbio-case-study-testdata
curl ${HTTPDIR}/HG002.pfda_challenge.grch38.phased.chr20.bam > input/Sniffles/sample2/HG002.pfda_challenge.grch38.phased.chr20.bam
curl ${HTTPDIR}/HG002.pfda_challenge.grch38.phased.chr20.bam.bai > input/Sniffles/sample2/HG002.pfda_challenge.grch38.phased.chr20.bam.bai
```

## Run

You can refer to the following bash script for a test under the `src` folder.

```bash
#!/bin/bash

# Define a list of queries
queries=(   
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market to train an LightGBM model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should give me the back test result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market (csi500) to train a LightGBM model. You should give me the back test result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market (csi300) to train a LightGBM model. You should give me the back test result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market (csi500) spanning from 2008 to 2018 to train an LightGBM model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should not only give me the back test result, but also the transaction details in csv format of how to get such result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market spanning from 2008 to 2018 to train a model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should not only give me the back test result, but also the transaction details of how to get such result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to train an LightGBM model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should give me the back test result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market spanning from 2008 to 2018 to train an LightGBM model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should give me the back test result.",
    "Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market to train an LightGBM model and get its backtest result. You should not only give me the back test result, but also the transaction details of how to get such result."
    )
gpt_version="""gpt-4-0125-preview"""

# Loop through each query and run the Python script
for query in """${queries[@]}"""
do
    echo """Processing: $query"""
    docker rmi $(docker images -f "dangling=true" -q)
    docker rm $(docker ps -a -f "status=exited" -q)
    python main.py --query "$query" --gpt_version $gpt_version --name "qlib_cot"
done
```

## Citation

If you think that OpenAct/OpenAgent is helpful, please cite it with:

```
@inproceedings{lyu2025enhancing,
    title={Enhancing Open-Domain Task-Solving Capability of LLMs via Autonomous Tool Integration from GitHub},
    author={Lyu, Bohan and Cong, Xin and Yu, Heyang and Yang, Pan and Qian, Cheng and Wang, Zihe and Qin, Yujia and Ye, Yining and Lu, Yaxi and Qian, Chen and others},
    booktitle={Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
    pages={17257--17277},
    year={2025}
}
```
