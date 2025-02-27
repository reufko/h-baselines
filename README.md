[![tests](https://github.com/AboudyKreidieh/h-baselines/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/AboudyKreidieh/h-baselines/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/AboudyKreidieh/h-baselines/badge.svg?branch=master)](https://coveralls.io/github/AboudyKreidieh/h-baselines?branch=master)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/AboudyKreidieh/h-baselines/blob/master/LICENSE)

# h-baselines

`h-baselines` is a repository of high-performing and benchmarked 
hierarchical reinforcement learning models and algorithms. This repository is 
motivated by, and partially adapted from, the 
[baselines](https://github.com/openai/baselines) and 
[stable-baselines](https://github.com/hill-a/stable-baselines) repositories.

You can learn more about the supported models and algorithms within this 
repository by reviewing this README.

## Contents

1. [Setup Instructions](#1-setup-instructions)  
    1.1. [Basic Installation](#11-basic-installation)  
    1.2. [Installing MuJoCo](#12-installing-mujoco)  
    1.3. [Importing AntGather](#13-importing-antgather)  
    1.4. [Installing Flow](#14-installing-flow)  
2. [Supported Models/Algorithms](#2-supported-modelsalgorithms)  
    2.1. [RL Algorithms](#21-rl-algorithms)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.1.1. [Synchronous Updates](#211-synchronous-updates)  
    2.2. [Fully Connected Neural Networks](#22-fully-connected-neural-networks)  
    2.3. [Goal-Conditioned HRL](#23-goal-conditioned-hrl)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.3.1. [Meta Period](#231-meta-period)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.3.2. [Intrinsic Rewards](#232-intrinsic-rewards)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.3.3. [HIRO (Data Efficient Hierarchical Reinforcement Learning)](#233-hiro-data-efficient-hierarchical-reinforcement-learning)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.3.4. [HAC (Learning Multi-level Hierarchies With Hindsight)](#234-hac-learning-multi-level-hierarchies-with-hindsight)  
        &nbsp; &nbsp; &nbsp;&nbsp; 2.3.5. [CHER (Inter-Level Cooperation in Hierarchical Reinforcement Learning)](#235-cher-inter-level-cooperation-in-hierarchical-reinforcement-learning)  
    2.4. [Multi-Agent Policies](#24-multi-agent-policies)  
3. [Environments](#3-environments)  
    3.1. [MuJoCo Environments](#31-mujoco-environments)  
    3.2. [Flow Environments](#32-flow-environments)  
4. [Citing](#4-citing)
5. [Bibliography](#5-bibliography)

# 1. Setup Instructions

## 1.1 Basic Installation

To install the h-baselines repository, begin by opening a terminal and set the
working directory of the terminal to match

```shell script
cd path/to/h-baselines
```

Next, create and activate a conda environment for this repository by running 
the commands in the script below. Note that this is not required, but highly 
recommended. If you do not have Anaconda on your device, refer to the provided
links to install either [Anaconda](https://www.anaconda.com/download) or
[Miniconda](https://conda.io/miniconda.html).

```shell script
conda env create -f environment.yml
source activate h-baselines
```

Finally, install the contents of the repository onto your conda environment (or
your local python build) by running the following command:

```shell script
pip install -e .
```

If you would like to (optionally) validate that the repository was successfully
installed and is running, you can do so by executing the unit tests as follows:

```shell script
nose2
```

The test should return a message along the lines of:

    ----------------------------------------------------------------------
    Ran XXX tests in YYYs

    OK

## 1.2 Installing MuJoCo

In order to run the MuJoCo environments described within the README, you
will need to install MuJoCo and the mujoco-py package. To install both
components follow the setup instructions located 
[here](https://github.com/openai/mujoco-py). This package should work 
with all versions of MuJoCo (with some changes likely to the version of 
`gym` provided); however, the algorithms have been benchmarked to 
perform well on `mujoco-py==1.50.1.68`.

## 1.3 Importing AntGather

To properly import and run the AntGather environment, you will need to 
first clone and install the `rllab` library. You can do so running the 
following commands:

```shell script
git clone https://github.com/rll/rllab.git
cd rllab
python setup.py develop
git submodule add -f https://github.com/florensacc/snn4hrl.git sandbox/snn4hrl
```

While all other environments run on all version of MuJoCo, this one will 
require MuJoCo-1.3.1. You may also need to install some missing packages
as well that are required by rllab. If you're installation is 
successful, the following command should not fail:

```shell script
python experiments/run_fcnet.py "AntGather"
```

When benchmarking this environment, we modified the control range and frame 
skip to match those used for the other Ant environments. If you would like to 
recreate these results and replay any pretrained policies, you will need to 
modify the rllab module such that the `git diff` of the repository returns
the following:

```
--- a/rllab/envs/mujoco/mujoco_env.py
+++ b/rllab/envs/mujoco/mujoco_env.py
@@ -82,6 +82,7 @@ class MujocoEnv(Env):
             size = self.model.numeric_size.flat[init_qpos_id]
             init_qpos = self.model.numeric_data.flat[addr:addr + size]
             self.init_qpos = init_qpos
+        self.frame_skip = 5
         self.dcom = None
         self.current_com = None
         self.reset()
diff --git a/vendor/mujoco_models/ant.xml b/vendor/mujoco_models/ant.xml
index 1ee575e..906f350 100644
--- a/vendor/mujoco_models/ant.xml
+++ b/vendor/mujoco_models/ant.xml
@@ -68,13 +68,13 @@
     </body>
   </worldbody>
   <actuator>
-    <motor joint="hip_4" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="ankle_4" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="hip_1" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="ankle_1" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="hip_2" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="ankle_2" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="hip_3" ctrlrange="-150.0 150.0" ctrllimited="true" />
-    <motor joint="ankle_3" ctrlrange="-150.0 150.0" ctrllimited="true" />
+    <motor joint="hip_4" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="ankle_4" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="hip_1" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="ankle_1" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="hip_2" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="ankle_2" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="hip_3" ctrlrange="-30.0 30.0" ctrllimited="true" />
+    <motor joint="ankle_3" ctrlrange="-30.0 30.0" ctrllimited="true" />
   </actuator>
 </mujoco>
```

## 1.4 Installing Flow

In order to run any of the mixed-autonomy traffic flow tasks describe 
[here](#32-flow-environments), you fill need to install the 
[flow](https://github.com/flow-project/flow) library, along with any necessary 
third-party tools. To do so, following the commands located on this 
[link](https://flow.readthedocs.io/en/latest/flow_setup.html#local-installation).
If your installation was successful, should run without failing:

```shell script
python experiments/run_fcnet.py "ring-v0"
```

Once you've installed Flow, you will also be able to run all training 
environments located in the flow/examples folder from this repository as well. 
These can be accessed by appending "flow:" to the environment name when running
the scripts in h-baselines/experiments. For example, if you would like to run 
the "singleagent_ring" environment in flow/example/rl/exp_configs, run:

```shell script
python experiments/run_fcnet.py "flow:singleagent_ring"
```

# 2. Supported Models/Algorithms

This repository currently supports the use several algorithms  of 
goal-conditioned hierarchical reinforcement learning models.

## 2.1 RL Algorithms

This repository supports the training of policies via two off-policy RL 
algorithms: [TD3](https://arxiv.org/pdf/1802.09477.pdf) and 
[SAC](https://arxiv.org/pdf/1801.01290.pdf), as well as two on-policy RL 
algorithms: [TRPO](https://arxiv.org/pdf/1502.05477.pdf) and 
[PPO](https://arxiv.org/pdf/1707.06347.pdf).

To train a policy using this algorithm, create a `RLAlgorithm` object 
and execute the `learn` method, providing the algorithm the proper policy 
along the process:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.fcnet.td3 import FeedForwardPolicy  # for TD3 algorithm

# create the algorithm object
alg = RLAlgorithm(policy=FeedForwardPolicy, env="AntGather")

# train the policy for the allotted number of timesteps
alg.learn(total_timesteps=1000000)
```

The specific algorithm that is executed is defined by the policy that is 
provided. If, for example, you would like to switch the above script to train 
a feed-forward policy using the SAC, TRPO, or PPO algorithms, then the policy 
must simply be changed to:

```python
from hbaselines.fcnet.sac import FeedForwardPolicy  # for SAC
from hbaselines.fcnet.trpo import FeedForwardPolicy  # for TRPO
from hbaselines.fcnet.ppo import FeedForwardPolicy  # for PPO
```

You can find the names of the hyperparameters and modifiable features of this 
algorithm by type in a python script `help(RLAlgorithm.__init__)`.

### 2.1.1 Synchronous Updates

This repository supports parallelism via synchronous updates to speed up 
training for environments that are relatively slow to simulate. In order to do 
so, a specified number of environments are instantiated and updated in parallel
for a number of rollout steps before calling the next policy update operation, 
as seen in the figure below. The number of environments in this case must be 
less than or equal to the number of rollout steps, as specified under 
`nb_rollout_steps`.

<p align="center"><img src="docs/img/synchronous-updates.png" align="middle" width="50%"/></p>

To assign multiple CPUs/environments for a given training algorithm, set the
`num_envs` term as seen below:

```python
from hbaselines.algorithms import RLAlgorithm

alg = RLAlgorithm(
    ...,
    # set num_envs as seen in the above figure
    num_envs=3,
    # set nb_rollout step as seen in the above figure
    nb_rollout_steps=5,
)
```

## 2.2 Fully Connected Neural Networks

We include a generic feed-forward neural network within the repository 
to validate the performance of typically used neural network model on 
the benchmarked environments. This consists of a pair of actor and 
critic fully connected networks with a tanh nonlinearity at the output 
layer of the actor. The output of the actors for the off-policy algorithms (TD3
and SAC) are also scaled to match the desired action space. 

The feed-forward policy can be imported by including the following 
script:

```python
# for TD3
from hbaselines.fcnet.td3 import FeedForwardPolicy

# for SAC
from hbaselines.fcnet.sac import FeedForwardPolicy

# for TRPO
from hbaselines.fcnet.trpo import FeedForwardPolicy

# for PPO
from hbaselines.fcnet.ppo import FeedForwardPolicy
```

This model can then be included to the algorithm via the `policy` parameter. 
You can find the input parameters for each of these policies by typing 
`help(FeedForwardPolicy.__init__)` once the desired policy has been imported.

When using the algorithm object, these parameters can be assigned by via the 
`policy_kwargs` term. For example, if you would like to train a fully connected
network using the TD3 algorithm with a hidden size of [64, 64], this could be 
done as such:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.fcnet.td3 import FeedForwardPolicy  # for TD3 algorithm

# create the algorithm object
alg = RLAlgorithm(
    policy=FeedForwardPolicy, 
    env="AntGather",
    policy_kwargs={
        # modify the network to include a hidden shape of [64, 64]
        "layers": [64, 64],
    }
)

# train the policy for the allotted number of timesteps
alg.learn(total_timesteps=1000000)
```

> All `policy_kwargs` terms that are not specified are assigned default 
> parameters. These default terms are available via the following command:
> 
> ```python
> from hbaselines.algorithms.rl_algorithm import FEEDFORWARD_PARAMS
> print(FEEDFORWARD_PARAMS)
> ```
> 
> Additional algorithm-specific default policy parameters can be found via the 
> following commands:
> 
> ```python
> # for TD3
> from hbaselines.algorithms.rl_algorithm import TD3_PARAMS
> print(TD3_PARAMS)
> 
> # for SAC
> from hbaselines.algorithms.rl_algorithm import SAC_PARAMS
> print(SAC_PARAMS)
> 
> # for TRPO
> from hbaselines.algorithms.rl_algorithm import TRPO_PARAMS
> print(TRPO_PARAMS)
> 
> # for PPO
> from hbaselines.algorithms.rl_algorithm import PPO_PARAMS
> print(PPO_PARAMS)
> ```

## 2.3 Goal-Conditioned HRL

<img align="right" src="docs/img/goal-conditioned.png" width="50%">

Goal-conditioned HRL models, also known as feudal models, are a variant of 
hierarchical models that have been widely studied in the HRL community. This 
repository supports a multi-level (2+ levels) variant of this policy, with a 
2-level version of this depicted in the figure to the right. This hierarchy 
consists of sequences of meta-policies, 
<img src="https://render.githubusercontent.com/render/math?math={\pi_i, \ i > 0}">, 
which assign goals to the policy within the hierarchy immediately below them, 
<img src="https://render.githubusercontent.com/render/math?math={\pi_{i-1}}">.
The lowest level within the hierarchy, 
<img src="https://render.githubusercontent.com/render/math?math={\pi_0}">, 
sometimes referred to as the *worker* 
policy, then performs environmental actions in an attempt to achieve the goal 
assigned to it within the environment.

The "goals" assigned by the meta-policies denote a desired state, or relative 
change in state, that is deemed advantageous by the meta-policies.  This behavior 
is then encouraged in the learning procedure via an intrinsic reward function: 
<img src="/tex/281172fc39903f7b030c2a37e355350d.svg?invert_in_darkmode&sanitize=true" align=middle width=102.71324744999998pt height=24.65753399999998pt/> 
(e.g. desired position to move to) which we further discuss in Section [2.3.2](#232-intrinsic-rewards). The highest level meta-policy receives 
the original environmental reward function 
<img src="/tex/8f3686f20d97a88b2ae16496f5e4cc6a.svg?invert_in_darkmode&sanitize=true" align=middle width=60.60137324999998pt height=24.65753399999998pt/>
to solve for the true objective of the assigned task.

The available algorithmic-specific variants of this policy can be imported in a
python script via the following command:

```python
# for TD3
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy

# for SAC
from hbaselines.goal_conditioned.sac import GoalConditionedPolicy
```

All the parameters specified within the 
[Fully Connected Neural Networks](#22-fully-connected-neural-networks) 
section are valid for this policy as well. Further relevant parameters are 
described in the subsequent sections below.

> Note: All `policy_kwargs` terms that are not specified are assigned default 
> parameters. These default terms are available via the following command:
>
> ```python
> from hbaselines.algorithms.rl_algorithm import GOAL_CONDITIONED_PARAMS
> print(GOAL_CONDITIONED_PARAMS)
> ```
> 
> Moreover, similar to the feed-forward policy, additional algorithm-specific 
> default policy parameters can be found via the following commands:
> 
> ```python
> # for TD3
> from hbaselines.algorithms.rl_algorithm import TD3_PARAMS
> print(TD3_PARAMS)
> 
> # for SAC
> from hbaselines.algorithms.rl_algorithm import SAC_PARAMS
> print(SAC_PARAMS)
> ```

### 2.3.1 Meta Period

The meta-policy action period is the number of a lower-level policy is assigned 
to perform the desired goal before it is assigned a new goal by the policy 
above it. It can be specified to the policy during training by passing the term 
under the `meta_period` policy parameter. This can be assigned through the 
algorithm as follows:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # specify the meta-policy action period
        "meta_period": 10
    }
)
```

### 2.3.2 Intrinsic Rewards

The intrinsic rewards, or <img src="/tex/281172fc39903f7b030c2a37e355350d.svg?invert_in_darkmode&sanitize=true" align=middle width=102.71324744999998pt height=24.65753399999998pt/>, define the rewards assigned
to the lower level policies for achieving goals assigned by the policies 
immediately above them. The choice of intrinsic reward can have a 
significant effect on the training performance of both the upper and lower 
level policies. Currently, this repository supports the use of two intrinsic 
reward functions:
 
* **negative_distance**: This is of the form:

  <p align="center"><img src="/tex/1689c3a6f75282843075ef0e3a4e87bb.svg?invert_in_darkmode&sanitize=true" align=middle width=226.09029464999998pt height=16.438356pt/></p>

  if `relative_goals` is set to False, and

  <p align="center"><img src="/tex/fa9c055e86f6927de37a480c240da337.svg?invert_in_darkmode&sanitize=true" align=middle width=259.67465205pt height=16.438356pt/></p>

  if `relative_goals` is set to True. This attribute is described in the 
[section on HIRO](#233-hiro-data-efficient-hierarchical-reinforcement-learning).

* **non_negative_distance**: This reward function is designed to maintain a 
  positive value within the intrinsic rewards to prevent the lower-level agents
  from being incentivized from falling/dying in environments that can terminate
  prematurely. This is done by offsetting the value by the maximum assignable 
  distance, assuming that the states always fall within the goal space 
  (<img src="/tex/47bed696feac0f0a4a4d81159c1140ec.svg?invert_in_darkmode&sanitize=true" align=middle width=29.62151939999999pt height=14.15524440000002pt/>, <img src="/tex/3308c39b78e1420bdfeb77271eeb8aa8.svg?invert_in_darkmode&sanitize=true" align=middle width=32.09870894999999pt height=14.15524440000002pt/>). This reward is of the form:

  <p align="center"><img src="/tex/099fe613c002c9305182bc0be946c803.svg?invert_in_darkmode&sanitize=true" align=middle width=355.27606784999995pt height=16.438356pt/></p>

  if `relative_goals` is set to False, and

  <p align="center"><img src="/tex/210fc43e0759bdc0a73bd4ea255fe30d.svg?invert_in_darkmode&sanitize=true" align=middle width=388.8604269pt height=16.438356pt/></p>

  if `relative_goals` is set to True. This attribute is described in the 
[section on HIRO](#233-hiro-data-efficient-hierarchical-reinforcement-learning).

* **exp_negative_distance**: This reward function is designed to maintain the 
  reward between 0 and 1 for environments that may terminate prematurely. This 
  is of the form:

  <p align="center"><img src="/tex/27bd484f07095bb27d59924ac338e719.svg?invert_in_darkmode&sanitize=true" align=middle width=285.17722695000003pt height=18.312383099999998pt/></p>

  if `relative_goals` is set to False, and

  <p align="center"><img src="/tex/e07e417d89f639d1d442eebff49421cc.svg?invert_in_darkmode&sanitize=true" align=middle width=318.76158599999997pt height=18.312383099999998pt/></p>

  if `relative_goals` is set to True. This attribute is described in the 
[section on HIRO](#233-hiro-data-efficient-hierarchical-reinforcement-learning).

Intrinsic rewards of the form above are not scaled by the any term, and as such
may be dominated by the largest term in the goal space. To circumvent this, we 
also include a scaled variant of each of the above intrinsic rewards were the 
states and goals are divided by goal space of the higher level policies. The 
new scaled rewards are then:

<p align="center"><img src="/tex/035cf72d718b01e1226cc5500d4f07ac.svg?invert_in_darkmode&sanitize=true" align=middle width=571.9927834499999pt height=33.58376834999999pt/></p>

where <img src="/tex/3308c39b78e1420bdfeb77271eeb8aa8.svg?invert_in_darkmode&sanitize=true" align=middle width=32.09870894999999pt height=14.15524440000002pt/> is the goal-space high values and <img src="/tex/47bed696feac0f0a4a4d81159c1140ec.svg?invert_in_darkmode&sanitize=true" align=middle width=29.62151939999999pt height=14.15524440000002pt/> are the 
goal-space low values. These intrinsic rewards can be used by initializing the 
string with "scaled_", for example: **scaled_negative_distance**, 
**scaled_non_negative_distance**, or **scaled_exp_negative_distance**.

To assign your choice of intrinsic rewards when training a hierarchical policy,
set the `intrinsic_reward_type` attribute to the type of intrinsic reward you 
would like to use:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # assign the intrinsic reward you would like to use
        "intrinsic_reward_type": "scaled_negative_distance"
    }
)
```

### 2.3.3 HIRO (Data Efficient Hierarchical Reinforcement Learning)

The HIRO [3] algorithm provides two primary contributions to improve 
training of generic goal-conditioned hierarchical policies. 

First of all, the HIRO algorithm redefines the assigned goals from 
absolute desired states to relative changes in states. This is done by 
redefining the reward intrinsic rewards provided to the Worker policies 
(see the [Intrinsic Rewards](#232-intrinsic-rewards) section). In order to 
maintain the same absolute position of the goal regardless of state 
change, a fixed goal-transition function 
<img src="/tex/39782c4f23877a296d304ed3de0aeda9.svg?invert_in_darkmode&sanitize=true" align=middle width=212.66347245pt height=24.65753399999998pt/> is used in between
goal-updates by the manager policy. The goal transition function is 
accordingly defined as:

<p align="center"><img src="/tex/30e3cd0420432be1c70aabbcd0ae9dd2.svg?invert_in_darkmode&sanitize=true" align=middle width=281.99380605pt height=49.315569599999996pt/></p>

where <img src="/tex/63bb9849783d01d91403bc9a5fea12a2.svg?invert_in_darkmode&sanitize=true" align=middle width=9.075367949999992pt height=22.831056599999986pt/> is the `meta_period`.

In order to use relative goals when training a hierarchical policy, set 
the `relative_goals` parameter to True:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # add this line to include HIRO-style relative goals
        "relative_goals": True
    }
)
```

Second, HIRO addresses the non-stationarity effects between the Manager and
Worker policies, which can have a detrimental effect particularly in off-policy 
training, by relabeling the manager actions (or goals) to make the actual 
observed action sequence more likely to have happened with respect to the 
current instantiation of the Worker policy. This is done by sampling a sequence
of potential goals sampled via a Gaussian centered at <img src="/tex/8ca069be1ef0c8a4237f18ccb2479810.svg?invert_in_darkmode&sanitize=true" align=middle width=62.22165014999998pt height=19.1781018pt/> and 
choosing the candidate goal that maximizes the log-probability of the actions 
that were originally performed by the Worker.

In order to use HIRO's goal relabeling (or off-policy corrections) procedure 
when training a hierarchical policy, set the `off_policy_corrections` parameter
to True:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # add this line to include HIRO-style off policy corrections
        "off_policy_corrections": True
    }
)
```

### 2.3.4 HAC (Learning Multi-level Hierarchies With Hindsight)

The HAC algorithm [5] attempts to address non-stationarity between levels of a 
goal-conditioned hierarchy by employing various forms of hindsight to samples 
within the replay buffer.

**Hindsight action transitions** assist by training each subgoal policy with 
respect to a transition function that simulates the optimal lower level policy 
hierarchy. This is done by by replacing the action performed by the manager 
with the subgoal state achieved in hindsight. For example, given an original 
sub-policy transition:

    sample = {
        "meta observation": s_0,
        "meta action" g_0,
        "meta reward" r,
        "worker observations" [
            (s_0, g_0),
            (s_1, h(g_0, s_0, s_1)),
            ...
            (s_k, h(g_{k-1}, s_{k-1}, s_k))
        ],
        "worker actions" [
            a_0,
            a_1,
            ...
            a_{k-1}
        ],
        "intrinsic rewards": [
            r_w(s_0, g_0, s_1),
            r_w(s_1, h(g_0, s_0, s_1), s_2),
            ...
            r_w(s_{k-1}, h(g_{k-1}, s_{k-1}, s_k), s_k)
        ]
    }

The original goal is relabeled to match the original as follows:

    sample = {
        "meta observation": s_0,
        "meta action" s_k, <---- the changed component
        "meta reward" r,
        "worker observations" [
            (s_0, g_0),
            (s_1, h(g_0, s_0, s_1)),
            ...
            (s_k, h(g_{k-1}, s_{k-1}, s_k))
        ],
        "worker actions" [
            a_0,
            a_1,
            ...
            a_{k-1}
        ],
        "intrinsic rewards": [
            r_w(s_0, g_0, s_1),
            r_w(s_1, h(g_0, s_0, s_1), s_2),
            ...
            r_w(s_{k-1}, h(g_{k-1}, s_{k-1}, s_k), s_k)
        ]
    }

In cases when the `relative_goals` feature is being employed, the hindsight 
goal is labeled using the inverse goal transition function. In other words, for
a sample with a meta period of length <img src="/tex/63bb9849783d01d91403bc9a5fea12a2.svg?invert_in_darkmode&sanitize=true" align=middle width=9.075367949999992pt height=22.831056599999986pt/>, the goal for every worker for every 
worker observation indexed by <img src="/tex/4f4f4e395762a3af4575de74c019ebb5.svg?invert_in_darkmode&sanitize=true" align=middle width=5.936097749999991pt height=20.221802699999984pt/> is:

<p align="center"><img src="/tex/b6c083237c42280c8a8c53351b15124e.svg?invert_in_darkmode&sanitize=true" align=middle width=247.02823364999998pt height=49.315569599999996pt/></p>

The "meta action", as represented in the example above, is then <img src="/tex/9053fd2f3aa4a20e3e837c3b0d414a34.svg?invert_in_darkmode&sanitize=true" align=middle width=14.393129849999989pt height=18.666631500000015pt/>.

**Hindsight goal transitions** extend the use of hindsight to the worker 
observations and intrinsic rewards within the sample as well. This is done by 
modifying the relevant worker-specific features as follows:

    sample = {
        "meta observation": s_0,
        "meta action" \bar{g}_0,
        "meta reward" r,
        "worker observations" [ <------------
            (s_0, \bar{g}_0),               |
            (s_1, \bar{g}_1),               |---- the changed components
            ...                             |
            (s_k, \bar{g}_k)                |
        ], <---------------------------------
        "worker actions" [
            a_0,
            a_1,
            ...
            a_{k-1}
        ],
        "intrinsic rewards": [ <-------------
            r_w(s_0, \bar{g}_0, s_1),       |
            r_w(s_1, \bar{g}_1,, s_2),      |---- the changed components
            ...                             |
            r_w(s_{k-1}, \bar{g}_k, s_k)    |
        ] <----------------------------------
    }

where <img src="/tex/cf330f355a2166e28d565ffff2400b3b.svg?invert_in_darkmode&sanitize=true" align=middle width=12.80637434999999pt height=18.666631500000015pt/> for <img src="/tex/cec901e2962c50e80af4cfde53675570.svg?invert_in_darkmode&sanitize=true" align=middle width=90.81016394999999pt height=24.65753399999998pt/> is equal to <img src="/tex/59efeb0f4f5d484a9b8a404d5bdac544.svg?invert_in_darkmode&sanitize=true" align=middle width=14.97150929999999pt height=14.15524440000002pt/> if `relative_goals`
is False and is defined by the equation above if set to True.

Finally, **sub-goal testing** promotes exploration when using hindsight by 
storing the original (non-hindsight) sample in the replay buffer as well. This 
happens at a rate defined by the `subgoal_testing_rate` term.

In order to use hindsight action and goal transitions when training a 
hierarchical policy, set the `hindsight` parameter to True:

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # include hindsight action and goal transitions in the replay buffer
        "hindsight": True,
        # specify the sub-goal testing rate
        "subgoal_testing_rate": 0.3
    }
)
```

### 2.3.5 CHER (Inter-Level Cooperation in Hierarchical Reinforcement Learning)

The CHER algorithm [4] attempts to promote cooperation between Manager
and Worker policies in a goal-conditioned hierarchy by including a 
weighted *cooperative gradient* term to the Manager's gradient update 
procedure (see the right figure below).

<p align="center"><img src="docs/img/hrl-cg.png" align="middle" width="90%"/></p>

Under this formulation, the Manager's update step is defined as:

<p align="center"><img src="/tex/ca9860e15619aaa5aa2687a72cf57a75.svg?invert_in_darkmode&sanitize=true" align=middle width=668.9097426pt height=68.9777022pt/></p>

To use the cooperative gradient update procedure, set the 
`cooperative_gradients` term in `policy_kwargs` to True. The weighting 
term (<img src="/tex/fd8be73b54f5436a5cd2e73ba9b6bfa9.svg?invert_in_darkmode&sanitize=true" align=middle width=9.58908224999999pt height=22.831056599999986pt/> in the above equation), can be modified via the 
`cg_weights` term (see the example below).

```python
from hbaselines.algorithms import RLAlgorithm
from hbaselines.goal_conditioned.td3 import GoalConditionedPolicy  # for TD3 algorithm

alg = RLAlgorithm(
    ...,
    policy=GoalConditionedPolicy,
    policy_kwargs={
        # add this line to include the cooperative gradient update procedure
        # for the higher-level policies
        "cooperative_gradients": True,
        # specify the cooperative gradient (lambda) weight
        "cg_weights": 0.01
    }
)
```

## 2.4 Multi-Agent Policies

This repository also supports the training of multi-agent variant of both the 
fully connected and goal-conditioned policies. The fully-connected policies are
import via the following commands:

```python
# for TD3
from hbaselines.multiagent.td3 import MultiFeedForwardPolicy

# for SAC
from hbaselines.multiagent.sac import MultiFeedForwardPolicy

# for TRPO
from hbaselines.multiagent.trpo import MultiFeedForwardPolicy

# for PPO
from hbaselines.multiagent.ppo import MultiFeedForwardPolicy
```

Moreover, the hierarchical variants are import via the following commands:

```python
# for TD3
from hbaselines.multiagent.h_td3 import MultiGoalConditionedPolicy

# for SAC
from hbaselines.multiagent.h_sac import MultiGoalConditionedPolicy
```

These policies support training three popular multi-agent algorithmic variants:

* **Independent learners**: Independent (or Naive) learners provide a separate
  policy with independent parameters to each agent in an environment.
  Within this setting, agents are provided separate observations and reward
  signals, and store their samples and perform updates separately. A review
  of independent learners in reinforcement learning can be found here:
  https://hal.archives-ouvertes.fr/hal-00720669/document

  To train a policy using independent learners, do not modify any
  policy-specific attributes:

  ```python
  from hbaselines.algorithms.rl_algorithm import RLAlgorithm
  from hbaselines.multiagent.td3 import MultiFeedForwardPolicy  # for TD3
  
  alg = RLAlgorithm(
      policy=MultiFeedForwardPolicy,
      env="...",  # replace with an appropriate environment
      policy_kwargs={}
  )
  ```

* **Shared policies**: Unlike the independent learners formulation, shared
  policies utilize a single policy with shared parameters for all agents
  within the network. Moreover, the samples experienced by all agents are
  stored within one unified replay buffer. See the following link for an
  early review of the benefit of shared policies:
  https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.55.8066&rep=rep1&type=pdf

  To train a policy using the shared policy feature, set the `shared`
  attribute to True:
  
  ```python
  from hbaselines.algorithms.rl_algorithm import RLAlgorithm
  from hbaselines.multiagent.td3 import MultiFeedForwardPolicy  # for TD3
  
  alg = RLAlgorithm(
      policy=MultiFeedForwardPolicy,
      env="...",  # replace with an appropriate environment
      policy_kwargs={
          "shared": True,
      }
  )
  ```

* **MADDPG**: We implement algorithmic-variants of MAPPG for all supported
  off-policy RL algorithms. See: https://arxiv.org/pdf/1706.02275.pdf

  To train a policy using their MADDPG variants as opposed to independent
  learners, algorithm, set the `maddpg` attribute to True:
  
  ```python
  from hbaselines.algorithms.rl_algorithm import RLAlgorithm
  from hbaselines.multiagent.td3 import MultiFeedForwardPolicy  # for TD3
  
  alg = RLAlgorithm(
      policy=MultiFeedForwardPolicy,
      env="...",  # replace with an appropriate environment
      policy_kwargs={
          "maddpg": True,
          "shared": False,  # or True
      }
  )
  ```

  This works for both shared and non-shared policies. For shared policies,
  we use a single centralized value function instead of a value function
  for each agent.

  > Note: MADDPG variants of the on-policy methods (TRPO and PPO) as well as 
  > the goal-conditioned hierarchies are currently not supported.

# 3. Environments

We benchmark the performance of all algorithms on a set of standardized 
[Mujoco](https://github.com/openai/mujoco-py) [7] (robotics) and 
[Flow](https://github.com/flow-project/flow) [8] (mixed-autonomy traffic) 
benchmarks. A description of each of the studied environments can be 
found below.

## 3.1 MuJoCo Environments

<img src="docs/img/mujoco-envs.png"/>

#### AntGather

This task was initially provided by [6].

In this task, a quadrupedal (Ant) agent is placed in a 20x20 space with 8 
apples and 8 bombs. The agent receives a reward of +1 or collecting an apple 
and -1 for collecting a bomb. All other actions yield a reward of 0.

#### AntMaze

This task was initially provided by [3].

In this task, immovable blocks are placed to confine the agent to a
U-shaped corridor. That is, blocks are placed everywhere except at (0,0), (8,0), 
(16,0), (16,8), (16,16), (8,16), and (0,16). The agent is initialized at 
position (0,0) and tasked at reaching a specific target position. "Success" in 
this environment is defined as being within an L2 distance of 5 from the target.

#### AntPush

This task was initially provided by [3].

In this task, immovable blocks are placed every where except at 
(0,0), (-8,0), (-8,8), (0,8), (8,8), (16,8), and (0,16), and a movable block is
placed at (0,8). The agent is initialized at position (0,0), and is tasked with 
the objective of reaching position (0,19). Therefore, the agent must first move 
to the left, push the movable block to the right, and then finally navigate to 
the target. "Success" in this environment is defined as being within an L2 
distance of 5 from the target.

#### AntFall

This task was initially provided by [3].

In this task, the agent is initialized on a platform of height 4. 
Immovable blocks are placed everywhere except at (-8,0), (0,0), (-8,8), (0,8),
(-8,16), (0,16), (-8,24), and (0,24). The raised platform is absent in the 
region [-4,12]x[12,20], and a movable block is placed at (8,8). The agent is 
initialized at position (0,0,4.5), and is with the objective of reaching 
position (0,27,4.5). Therefore, to achieve this, the agent must first push the 
movable block into the chasm and walk on top of it before navigating to the 
target. "Success" in this environment is defined as being within an L2 distance 
of 5 from the target.

## 3.2 Flow Environments

We also explore the use of hierarchical policies on a suite of mixed-autonomy
traffic control tasks, built off the [Flow](https://github.com/flow-project/flow.git) 
[8] framework for RL in microscopic (vehicle-level) traffic simulators. Within 
these environments, a subset of vehicles in any given network are replaced with
"automated" vehicles whose actions are provided on an RL policy. A description 
of the attributes of the MDP within these tasks is provided in the following 
subsections. Additional information can be found through the 
[environment classes](https://github.com/AboudyKreidieh/h-baselines/tree/master/hbaselines/envs/mixed_autonomy/envs) 
and 
[flow-specific parameters](https://github.com/AboudyKreidieh/h-baselines/tree/master/hbaselines/envs/mixed_autonomy/params).

<p align="center"><img src="docs/img/flow-envs-3.png" align="middle" width="100%"/></p>

The below table describes all available tasks within this repository to train 
on. Any of these environments can be used by passing the environment name to 
the `env` parameter in the algorithm class. The multi-agent variants of these 
environments can also be trained by adding "multiagent-" to the start of the 
environment name (e.g. "multiagent-ring-v0").

| Network type        | Environment name | number of AVs | total vehicles |  AV ratio   | inflow rate (veh/hr) | acceleration penalty | stopping penalty |
|---------------------|------------------|:-------------:|:--------------:|:-----------:|:--------------------:|:--------------------:|:----------------:|
| [ring](#ring)       | ring             |       1       |       22       |    1/22     |          --          |         yes          |       yes        |
| [merge](#merge)     | merge-v0         |      ~5       |      ~50       |    1/10     |         2000         |         yes          |        no        |
|                     | merge-v1         |      ~13      |      ~50       |     1/4     |         2000         |         yes          |        no        |
|                     | merge-v2         |      ~17      |      ~50       |     1/3     |         2000         |         yes          |        no        |
| [highway](#highway) | highway-v0       |      ~10      |      ~150      |    1/12     |         2215         |         yes          |       yes        |
|                     | highway-v1       |      ~10      |      ~150      |    1/12     |         2215         |         yes          |        no        |
|                     | highway-v2       |      ~10      |      ~150      |    1/12     |         2215         |          no          |        no        |
| [I-210](#i-210)     | i210-v0          |      ~50      |      ~800      |    1/15     |        10250         |         yes          |       yes        |
|                     | i210-v1          |      ~50      |      ~800      |    1/15     |        10250         |         yes          |        no        |
|                     | i210-v2          |      ~50      |      ~800      |    1/15     |        10250         |          no          |        no        |

### States

The state for any of these environments consists of the speeds and 
bumper-to-bumper gaps of the vehicles immediately preceding and following the 
AVs, as well as the speed of the AVs, i.e. 
<img src="/tex/b5e79a57244c545109a7bdf53379f6f6.svg?invert_in_darkmode&sanitize=true" align=middle width=306.54702045pt height=24.65753399999998pt/>.
In single agent settings, these observations are concatenated in a single 
observation that is passed to a centralized policy.

In order to account for variability in the number of AVs (<img src="/tex/bb1a6273b87d3166c04533f3fb19f5ec.svg?invert_in_darkmode&sanitize=true" align=middle width=28.034803499999988pt height=14.15524440000002pt/>) in the
single agent setting, a constant <img src="/tex/b11a49d39a5e2710e2f8fe3f57fe5afb.svg?invert_in_darkmode&sanitize=true" align=middle width=27.53820629999999pt height=14.15524440000002pt/> term is defined. When 
<img src="/tex/4efa77061e9a739b3ab8d64fa6ca3417.svg?invert_in_darkmode&sanitize=true" align=middle width=78.13562129999998pt height=17.723762100000005pt/>, information from the extra CAVs are not included 
in the state. Moreover, if <img src="/tex/9d6b99d3ad4c82ddc70cfdc1820a7968.svg?invert_in_darkmode&sanitize=true" align=middle width=87.51922574999999pt height=17.723762100000005pt/> the state is padded 
with zeros.

### Actions

The actions consist of a list of bounded accelerations for each AV, i.e. 
<img src="/tex/1368ce716be6f77aa6743627a917f029.svg?invert_in_darkmode&sanitize=true" align=middle width=106.88881004999998pt height=26.76175259999998pt/>, where <img src="/tex/7de57cd5f7a02a410bbf4ad74bbee46c.svg?invert_in_darkmode&sanitize=true" align=middle width=30.47008964999999pt height=14.15524440000002pt/> and 
<img src="/tex/274597d9a192abe37c32f87bef1300b6.svg?invert_in_darkmode&sanitize=true" align=middle width=32.947280849999984pt height=14.15524440000002pt/> are the minimum and maximum accelerations, respectively. In the 
single agent setting, all actions are provided as an output from a single 
policy.

Once again, an <img src="/tex/b11a49d39a5e2710e2f8fe3f57fe5afb.svg?invert_in_darkmode&sanitize=true" align=middle width=27.53820629999999pt height=14.15524440000002pt/> term is used to handle variable numbers of AVs in
the single agent setting. If <img src="/tex/4efa77061e9a739b3ab8d64fa6ca3417.svg?invert_in_darkmode&sanitize=true" align=middle width=78.13562129999998pt height=17.723762100000005pt/> the extra AVs are 
treated as human-driven vehicles and their states are updated using human 
driver models. Moreover, if <img src="/tex/5625b4db53cd16eaf50ac1874d3c9f15.svg?invert_in_darkmode&sanitize=true" align=middle width=78.13562129999998pt height=17.723762100000005pt/>, the extra actions are
ignored.

### Rewards

The reward provided by the environment is equal to the negative vector normal 
of the distance between the speed of all vehicles in the network and a desired 
speed, and is offset by largest possible negative term to ensure non-negativity
if environments terminate prematurely. The exact mathematical formulation of 
this reward is:

<p align="center"><img src="/tex/2bf655f3f70c50002913f79c86690bc6.svg?invert_in_darkmode&sanitize=true" align=middle width=327.91753665pt height=16.438356pt/></p>

where <img src="/tex/6c4adbc36120d62b98deef2a20d5d303.svg?invert_in_darkmode&sanitize=true" align=middle width=8.55786029999999pt height=14.15524440000002pt/> is the speed of the individual vehicles, <img src="/tex/f5f76957f34c6277702156f93f1d35ea.svg?invert_in_darkmode&sanitize=true" align=middle width=26.280957449999992pt height=14.15524440000002pt/> is the 
desired speed, and <img src="/tex/55a049b8f161ae7cfeb0197d75aff967.svg?invert_in_darkmode&sanitize=true" align=middle width=9.86687624999999pt height=14.15524440000002pt/> is the number of vehicles in the network.

This reward may only include two penalties:

* **acceleration penalty:** If set to True in env_params, the negative of the 
  sum of squares of the accelerations by the AVs is added to the reward.
* **stopping penalty:** If set to True in env_params, a penalty of -5 is added 
  to the reward for every RL vehicle that is not moving.

### Networks

We investigate the performance of our algorithms on a variety of network 
configurations demonstrating diverse traffic instabilities and forms of 
congestion. This networks are detailed below.

#### ring

This scenario consists of 22 vehicles (1 of which are automated) on a sing-lane
circular track of length 220-270 m. In the absence of the automated vehicle, 
the human-driven vehicles exhibit stop-and-go instabilities brought about by 
the string-unstable characteristic of human car-following dynamics.

#### merge

This scenarios is adapted from the following article [9]. It consists of a 
single-lane highway network with an on-ramp used to generate periodic 
perturbations to sustain congested behavior. In order to model the effect of p%
AV penetration on the network, every 100/pth vehicle is replaced with an 
automated vehicle whose actions are sampled from an RL policy.

#### highway

This scenario consists of a single lane highway in which downstream traffic 
instabilities brought about by an edge with a reduced speed limit generate 
congestion in the form of stop-and-go waves. In order to model the effect of p%
AV penetration on the network, every 100/pth vehicle is replaced with an 
automated vehicle whose actions are sampled from an RL policy.

#### I-210

This scenario is a recreation of a subsection of the I-210 network in Los 
Angeles, CA. For the moment, the on-ramps and off-ramps are disabled within 
this network, rendering it similar to a multi-lane variant of the highway 
network.

# 4. Citing

To cite this repository in publications, use the following:

Kreidieh, Abdul Rahman, et al. "Inter-Level Cooperation in Hierarchical 
Reinforcement Learning." arXiv preprint arXiv:1912.02368 (2019). [Online]. 
Available: https://arxiv.org/abs/1912.02368

# 5. Bibliography

[1] Dayan, Peter, and Geoffrey E. Hinton. "Feudal reinforcement learning." 
Advances in neural information processing systems. 1993.

[2] Vezhnevets, Alexander Sasha, et al. "Feudal networks for hierarchical 
reinforcement learning." Proceedings of the 34th International Conference on 
Machine Learning-Volume 70. JMLR. org, 2017.

[3] Nachum, Ofir, et al. "Data-efficient hierarchical reinforcement learning."
Advances in Neural Information Processing Systems. 2018.

[4] Kreidieh, Abdul Rahmnan, et al. "Inter-Level Cooperation in Hierarchical 
Reinforcement Learning". arXiv preprint arXiv:1912.02368 (2019).

[5] Levy, Andrew, et al. "Learning Multi-Level Hierarchies with Hindsight." 
(2018).

[6] Florensa, Carlos, Yan Duan, and Pieter Abbeel. "Stochastic neural 
networks for hierarchical reinforcement learning." arXiv preprint 
arXiv:1704.03012 (2017).

[7] Todorov, Emanuel, Tom Erez, and Yuval Tassa. "Mujoco: A physics engine for 
model-based control." 2012 IEEE/RSJ International Conference on Intelligent 
Robots and Systems. IEEE, 2012.

[8] Wu, Cathy, et al. "Flow: A Modular Learning Framework for Autonomy 
in Traffic." arXiv preprint arXiv:1710.05465 (2017).

[9] Kreidieh, Abdul Rahman, Cathy Wu, and Alexandre M. Bayen. "Dissipating 
stop-and-go waves in closed and open networks via deep reinforcement learning."
2018 21st International Conference on Intelligent Transportation Systems 
(ITSC). IEEE, 2018.
