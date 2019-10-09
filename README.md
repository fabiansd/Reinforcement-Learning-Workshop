[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

[cc-by-nc-sa]: https://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-shield]: https://mirrors.creativecommons.org/presskit/buttons/80x15/svg/by-nc-sa.svg

# Reinforcement-Learning-Workshop
Necessary files and notebooks to host a RL workshop on AWS

## AWS

### Setup

An AWS Image is used to create a docker container with the reinforcement learning environment, and automatically launch a Jupyter Notebook on port 8888. To access this notebook, a link is generated with the corresponding IP, port and token.

### Steps to launch instances for the WS

1. Select number of instances to start
2. Paste in the user data
3. Remember to attach the correct network security group (which opens up port 8888) and IAM role (to give write access to s3)

### Visualization
Visualizations in the DQN-notebooks are only supported for Linux and OSX, in addition to headless Linux servers, e.g. an AWS EC2 Linux instance. 
