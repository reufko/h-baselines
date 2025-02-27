"""Base goal-conditioned hierarchical policy."""
import tensorflow as tf
import numpy as np
from copy import deepcopy
import os
import random
from functools import reduce

from hbaselines.base_policies import Policy
from hbaselines.goal_conditioned.replay_buffer import HierReplayBuffer
from hbaselines.utils.reward_fns import negative_distance
from hbaselines.utils.env_util import get_meta_ac_space, get_state_indices
from hbaselines.utils.tf_util import get_trainable_vars


class GoalConditionedPolicy(Policy):
    """Goal-conditioned hierarchical reinforcement learning model.

    Attributes
    ----------
    num_levels : int
        number of levels within the hierarchy. Must be greater than 1. Two
        levels correspond to a Manager/Worker paradigm.
    meta_period : int or [int]
        meta-policy action period. For multi-level hierarchies, a separate meta
        period can be provided for each level (indexed from highest to lowest)
    intrinsic_reward_type : str
        the reward function to be used by the worker. Must be one of:

        * "negative_distance": the negative two norm between the states and
          desired absolute or relative goals.
        * "scaled_negative_distance": similar to the negative distance reward
          where the states, goals, and next states are scaled by the inverse of
          the action space of the manager policy
        * "non_negative_distance": the negative two norm between the states and
          desired absolute or relative goals offset by the maximum goal space
          (to ensure non-negativity)
        * "scaled_non_negative_distance": similar to the non-negative distance
          reward where the states, goals, and next states are scaled by the
          inverse of the action space of the manager policy
        * "exp_negative_distance": equal to exp(-negative_distance^2). The
          result is a reward between 0 and 1. This is useful for policies that
          terminate early.
        * "scaled_exp_negative_distance": similar to the previous worker reward
          type but with states, actions, and next states that are scaled.
    intrinsic_reward_scale : [float]
        the value that the intrinsic reward should be scaled by. One for each
        meta-level.
    relative_goals : bool
        specifies whether the goal issued by the higher-level policies is meant
        to be a relative or absolute goal, i.e. specific state or change in
        state
    off_policy_corrections : bool
        whether to use off-policy corrections during the update procedure. See:
        https://arxiv.org/abs/1805.08296.
    hindsight : bool
        whether to use hindsight action and goal transitions, as well as
        subgoal testing. See: https://arxiv.org/abs/1712.00948
    subgoal_testing_rate : float
        rate at which the original (non-hindsight) sample is stored in the
        replay buffer as well. Used only if `hindsight` is set to True.
    cooperative_gradients : bool
        whether to use the cooperative gradient update procedure for the
        higher-level policy. See: https://arxiv.org/abs/1912.02368v1
    cg_weights : float
        weights for the gradients of the loss of the lower-level policies with
        respect to the parameters of the higher-level policies. Only used if
        `cooperative_gradients` is set to True.
    pretrain_worker : bool
        specifies whether you are pre-training the lower-level policies.
        Actions by the high-level policy are randomly sampled from its action
        space.
    pretrain_path : str or None
        path to the pre-trained worker policy checkpoints
    pretrain_ckpt : int or None
        checkpoint number to use within the worker policy path. If set to None,
        the most recent checkpoint is used.
    total_steps : int
        Total number of timesteps used during training. Used by a subset of
        algorithms.
    policy : list of hbaselines.base_policies.Policy
        a list of policy object for each level in the hierarchy, order from
        highest to lowest level policy
    replay_buffer : hbaselines.goal_conditioned.replay_buffer.HierReplayBuffer
        the replay buffer object
    goal_indices : list of int
        the state indices for the intrinsic rewards
    intrinsic_reward_fn : function
        reward function for the lower-level policies
    """

    def __init__(self,
                 sess,
                 ob_space,
                 ac_space,
                 co_space,
                 buffer_size,
                 batch_size,
                 actor_lr,
                 critic_lr,
                 verbose,
                 tau,
                 gamma,
                 use_huber,
                 l2_penalty,
                 model_params,
                 num_levels,
                 meta_period,
                 intrinsic_reward_type,
                 intrinsic_reward_scale,
                 relative_goals,
                 off_policy_corrections,
                 hindsight,
                 subgoal_testing_rate,
                 cooperative_gradients,
                 cg_weights,
                 cg_delta,
                 pretrain_worker,
                 pretrain_path,
                 pretrain_ckpt,
                 total_steps,
                 scope=None,
                 env_name="",
                 num_envs=1,
                 meta_policy=None,
                 worker_policy=None,
                 additional_params=None):
        """Instantiate the goal-conditioned hierarchical policy.

        Parameters
        ----------
        sess : tf.compat.v1.Session
            the current TensorFlow session
        ob_space : gym.spaces.*
            the observation space of the environment
        ac_space : gym.spaces.*
            the action space of the environment
        co_space : gym.spaces.*
            the context space of the environment
        buffer_size : int
            the max number of transitions to store
        batch_size : int
            SGD batch size
        actor_lr : float
            actor learning rate
        critic_lr : float
            critic learning rate
        verbose : int
            the verbosity level: 0 none, 1 training information, 2 tensorflow
            debug
        tau : float
            target update rate
        gamma : float
            discount factor
        use_huber : bool
            specifies whether to use the huber distance function as the loss
            for the critic. If set to False, the mean-squared error metric is
            used instead
        model_params : dict
            dictionary of model-specific parameters. See parent class.
        num_levels : int
            number of levels within the hierarchy. Must be greater than 1. Two
            levels correspond to a Manager/Worker paradigm.
        meta_period : int or [int]
            meta-policy action period. For multi-level hierarchies, a separate
            meta period can be provided for each level (indexed from highest to
            lowest)
        intrinsic_reward_type : str
            the reward function to be used by the worker. Must be one of:

            * "negative_distance": the negative two norm between the states and
              desired absolute or relative goals.
            * "scaled_negative_distance": similar to the negative distance
              reward where the states, goals, and next states are scaled by the
              inverse of the action space of the manager policy
            * "non_negative_distance": the negative two norm between the states
              and desired absolute or relative goals offset by the maximum goal
              space (to ensure non-negativity)
            * "scaled_non_negative_distance": similar to the non-negative
              distance reward where the states, goals, and next states are
              scaled by the inverse of the action space of the manager policy
            * "exp_negative_distance": equal to exp(-negative_distance^2). The
              result is a reward between 0 and 1. This is useful for policies
              that terminate early.
            * "scaled_exp_negative_distance": similar to the previous worker
              reward type but with states, actions, and next states that are
              scaled.
        intrinsic_reward_scale : float or [float]
            the value that the intrinsic reward should be scaled by. One for
            each lower-level.
        relative_goals : bool
            specifies whether the goal issued by the higher-level policies is
            meant to be a relative or absolute goal, i.e. specific state or
            change in state
        off_policy_corrections : bool
            whether to use off-policy corrections during the update procedure.
            See: https://arxiv.org/abs/1805.08296
        hindsight : bool
            whether to include hindsight action and goal transitions in the
            replay buffer. See: https://arxiv.org/abs/1712.00948
        subgoal_testing_rate : float
            rate at which the original (non-hindsight) sample is stored in the
            replay buffer as well. Used only if `hindsight` is set to True.
        cooperative_gradients : bool
            whether to use the cooperative gradient update procedure for the
            higher-level policy. See: https://arxiv.org/abs/1912.02368v1
        cg_weights : float
            weights for the gradients of the loss of the lower-level policies
            with respect to the parameters of the higher-level policies. Only
            used if `cooperative_gradients` is set to True.
        cg_delta : float
            the desired lower-level expected returns. If set to None, a fixed
            Lagrangian specified by cg_weights is used instead. Only used if
            `cooperative_gradients` is set to True.
        pretrain_worker : bool
            specifies whether you are pre-training the lower-level policies.
            Actions by the high-level policy are randomly sampled from the
            action space.
        pretrain_path : str or None
            path to the pre-trained worker policy checkpoints
        pretrain_ckpt : int or None
            checkpoint number to use within the worker policy path. If set to
            None, the most recent checkpoint is used.
        total_steps : int
            Total number of timesteps used during training. Used by a subset of
            algorithms.
        meta_policy : type [ hbaselines.base_policies.Policy ]
            the policy model to use for the meta policies
        worker_policy : type [ hbaselines.base_policies.Policy ]
            the policy model to use for the worker policy
        additional_params : dict
            additional algorithm-specific policy parameters. Used internally by
            the class when instantiating other (child) policies.
        """
        super(GoalConditionedPolicy, self).__init__(
            sess=sess,
            ob_space=ob_space,
            ac_space=ac_space,
            co_space=co_space,
            verbose=verbose,
            l2_penalty=l2_penalty,
            model_params=model_params,
            num_envs=num_envs,
        )

        # Run assertions.
        assert num_levels >= 2, "num_levels must be greater than or equal to 2"
        if off_policy_corrections:
            assert num_levels == 2, \
                "Off-policy collections only work for two-level hierarchies."
        if hindsight:
            assert num_levels == 2, \
                "Hindsight only work for two-level hierarchies."

        # Process some variable.
        if isinstance(meta_period, list) and len(meta_period) == 1:
            meta_period = meta_period[0]
        if isinstance(intrinsic_reward_scale, float):
            intrinsic_reward_scale = [
                intrinsic_reward_scale for _ in range(num_levels - 1)]

        self.num_levels = num_levels
        self.meta_period = meta_period
        self.intrinsic_reward_type = intrinsic_reward_type
        self.intrinsic_reward_scale = intrinsic_reward_scale
        self.relative_goals = relative_goals
        self.off_policy_corrections = off_policy_corrections
        self.hindsight = hindsight
        self.subgoal_testing_rate = subgoal_testing_rate
        self.cooperative_gradients = cooperative_gradients
        self.cg_weights = cg_weights
        self.cg_delta = cg_delta
        self.pretrain_worker = pretrain_worker
        self.pretrain_path = pretrain_path
        self.pretrain_ckpt = pretrain_ckpt
        self.total_steps = total_steps

        # Get the observation and action space of the higher level policies.
        meta_ac_space = get_meta_ac_space(
            ob_space=ob_space,
            relative_goals=relative_goals,
            env_name=env_name,
        )

        # =================================================================== #
        # Step 1: Create the policies for the individual levels.              #
        # =================================================================== #

        self.policy = []

        # The policies are ordered from the highest level to lowest level
        # policies in the hierarchy.
        for i in range(num_levels):
            # Determine the appropriate parameters to use for the policy in the
            # current level.
            policy_fn = meta_policy if i < (num_levels - 1) else worker_policy
            ac_space_i = meta_ac_space if i < (num_levels - 1) else ac_space
            co_space_i = co_space if i == 0 else meta_ac_space
            ob_space_i = ob_space

            # The policies are ordered from the highest level to lowest level
            # policies in the hierarchy.
            with tf.compat.v1.variable_scope("level_{}".format(i)):
                # Compute the scope name based on any outer scope term.
                scope_i = "level_{}".format(i)
                if scope is not None:
                    scope_i = "{}/{}".format(scope, scope_i)

                model_params_i = model_params.copy()
                model_params_i.update({
                    "ignore_flat_channels":
                        model_params["ignore_flat_channels"] if i < 1 else [],
                    "ignore_image":
                        model_params["ignore_image"] if i < 1 else True,
                })

                # Create the next policy.
                self.policy.append(policy_fn(
                    sess=sess,
                    ob_space=ob_space_i,
                    ac_space=ac_space_i,
                    co_space=co_space_i,
                    buffer_size=buffer_size,
                    batch_size=batch_size,
                    actor_lr=actor_lr,
                    critic_lr=critic_lr,
                    verbose=verbose,
                    tau=tau,
                    gamma=gamma,
                    use_huber=use_huber,
                    l2_penalty=l2_penalty,
                    model_params=model_params_i,
                    scope=scope_i,
                    **(additional_params or {}),
                ))

        # =================================================================== #
        # Step 2: Create attributes for the replay buffer.                    #
        # =================================================================== #

        # Create the replay buffer.
        self.replay_buffer = HierReplayBuffer(
            buffer_size=int(buffer_size/(
                meta_period ** num_levels - 1 if isinstance(meta_period, int)
                else reduce((lambda x, y: x*y), self.meta_period))),
            batch_size=batch_size,
            meta_period=meta_period,
            obs_dim=ob_space.shape[0],
            ac_dim=ac_space.shape[0],
            co_dim=None if co_space is None else co_space.shape[0],
            goal_dim=meta_ac_space.shape[0],
            num_levels=num_levels
        )

        # current action by the meta-level policies
        self.meta_action = [[None for _ in range(num_levels - 1)]
                            for _ in range(num_envs)]

        # a list of all the actions performed by each level in the hierarchy,
        # ordered from highest to lowest level policy. A separate element is
        # used for each environment.
        self._actions = [[[] for _ in range(self.num_levels)]
                         for _ in range(num_envs)]

        # a list of the rewards (intrinsic or other) experienced by every level
        # in the hierarchy, ordered from highest to lowest level policy. A
        # separate element is used for each environment.
        self._rewards = [[[0]] + [[] for _ in range(self.num_levels - 1)]
                         for _ in range(num_envs)]

        # a list of observations that stretch as long as the dilated horizon
        # chosen for the highest level policy. A separate element is used for
        # each environment.
        self._observations = [[] for _ in range(num_envs)]

        # the first and last contextual term. A separate element is used for
        # each environment.
        self._contexts = [[] for _ in range(num_envs)]

        # a list of done masks at every time step. A separate element is used
        # for each environment.
        self._dones = [[] for _ in range(num_envs)]

        # Collect the state indices for the intrinsic rewards.
        self.goal_indices = get_state_indices(ob_space, env_name)

        # Define the intrinsic reward function.
        if intrinsic_reward_type in ["negative_distance",
                                     "scaled_negative_distance",
                                     "non_negative_distance",
                                     "scaled_non_negative_distance",
                                     "exp_negative_distance",
                                     "scaled_exp_negative_distance"]:
            # Offset the distance measure by the maximum possible distance to
            # ensure non-negativity.
            if "non_negative" in intrinsic_reward_type:
                offset = np.sqrt(np.sum(np.square(
                    meta_ac_space.high - meta_ac_space.low), -1))
            else:
                offset = 0

            # Scale the outputs from the state by the meta-action space if you
            # wish to scale the worker reward.
            if intrinsic_reward_type.startswith("scaled"):
                scale = 0.5 * (meta_ac_space.high - meta_ac_space.low)
            else:
                scale = 1

            def intrinsic_reward_fn(states, goals, next_states):
                return negative_distance(
                    states=states[self.goal_indices] / scale,
                    goals=goals / scale,
                    next_states=next_states[self.goal_indices] / scale,
                    relative_context=relative_goals,
                    offset=0.0,
                ) + offset

            # Perform the exponential and squashing operations to keep the
            # intrinsic reward between 0 and 1.
            if "exp" in intrinsic_reward_type:
                def exp_intrinsic_reward_fn(states, goals, next_states):
                    span = sum(np.square(self.policy[0].ac_space.high -
                                         self.policy[0].ac_space.low))
                    rew = intrinsic_reward_fn(states, goals, next_states)
                    return np.exp(- (rew / (span / 40)) ** 2)
                self.intrinsic_reward_fn = exp_intrinsic_reward_fn
            else:
                self.intrinsic_reward_fn = intrinsic_reward_fn
        else:
            raise ValueError("Unknown intrinsic reward type: {}".format(
                intrinsic_reward_type))

        # =================================================================== #
        # Step 3: Create algorithm-specific features.                         #
        # =================================================================== #

        # the number of get_action calls that have been performed. This is used
        # when pretraining the worker to incrementally train different levels
        # of the policy.
        self._steps = 0

        # a fixed goal transition function for the meta-actions in between meta
        # periods. This is used when relative_goals is set to True in order to
        # maintain a fixed absolute position of the goal.
        if relative_goals:
            def goal_transition_fn(obs0, goal, obs1):
                return obs0 + goal - obs1
        else:
            def goal_transition_fn(obs0, goal, obs1):
                return goal
        self.goal_transition_fn = goal_transition_fn

        if self.cooperative_gradients:
            if scope is None:
                self._setup_cooperative_gradients()
            else:
                with tf.compat.v1.variable_scope(scope):
                    self._setup_cooperative_gradients()

    def initialize(self):
        """See parent class.

        This method performs the following operations:

        - It calls the initialization methods of the policies at every level of
          the hierarchy to match the target value function parameters with the
          current policy parameters.
        - It also imports the lower-level policies from a pretrained checkpoint
          if a path to one is specified.
        """
        # Initialize the separate policies in the hierarchy.
        for i in range(self.num_levels):
            self.policy[i].initialize()

        if self.pretrain_path is not None:
            ckpt_path = os.path.join(self.pretrain_path, "checkpoints")

            # Get the checkpoint number.
            if self.pretrain_ckpt is None:
                filenames = os.listdir(ckpt_path)
                metafiles = [f[:-5] for f in filenames if f[-5:] == ".meta"]
                metanum = [int(f.split("-")[-1]) for f in metafiles]
                ckpt_num = max(metanum)
            else:
                ckpt_num = self.pretrain_ckpt

            # Extract the checkpoint path.
            ckpt_path = os.path.join(ckpt_path, "itr-{}".format(ckpt_num))
            var_list = tf.train.list_variables(ckpt_path)
            ckpt_reader = tf.train.load_checkpoint(ckpt_path)

            # Check that the number of levels match.
            assert var_list[-1][0].startswith(
                "level_{}".format(self.num_levels-1)), \
                "Number of levels between the checkpoint and current policy " \
                "do not match. Policy={}, Checkpoint={}".format(
                    self.num_levels,
                    int(var_list[-1][0].split("/")[0][6:]) + 1)

            # Check that the names and shapes of the lowest-level policy
            # parameters match the current policy.
            current_vars = {
                v.name: v.shape.as_list()
                for v in get_trainable_vars()
            }
            for var in var_list:
                var_name, var_shape = var
                var_name = "{}:0".format(var_name)
                # We only check the lower-level policies.
                if any(var_name.startswith("level_{}".format(level))
                       for level in range(1, self.num_levels)):
                    assert var_name in current_vars.keys(), \
                        "{} not available in current policy.".format(var_name)
                    current_shape = current_vars[var_name]
                    assert current_shape == var_shape, \
                        "Shape mismatch for {}, {} != {}".format(
                            var_name, var_shape, current_shape)

            # Import the lower-level policy parameters.
            current_vars = {v.name: v for v in get_trainable_vars()}
            for var in var_list:
                var_name, var_shape = var
                if any(var_name.startswith("level_{}".format(level))
                       for level in range(1, self.num_levels)):
                    value = ckpt_reader.get_tensor(var_name)
                    var_name = "{}:0".format(var_name)
                    self.sess.run(
                        tf.compat.v1.assign(current_vars[var_name], value))

    def update(self, update_actor=True, **kwargs):
        """Perform a gradient update step.

        This is done both at every level of the hierarchy.

        The kwargs argument for this method contains two additional terms:

        * update_meta (bool): specifies whether to perform a gradient update
          step for the meta-policies
        * update_meta_actor (bool): similar to the `update_policy` term, but
          for the meta-policy. Note that, if `update_meta` is set to False,
          this term is void.

        **Note**; The target update soft updates for all policies occur at the
        same frequency as their respective actor update frequencies.

        Parameters
        ----------
        update_actor : bool
            specifies whether to update the actor policy. The critic policy is
            still updated if this value is set to False.
        """
        # Not enough samples in the replay buffer.
        if not self.replay_buffer.can_sample():
            return

        # Specifies whether to remove additional data from the replay buffer
        # sampling procedure. Since only a subset of algorithms use additional
        # data, removing it can speedup the other algorithms.
        with_additional = self.off_policy_corrections

        # Specifies the levels to collect data from, corresponding to the
        # levels that will be trained. This also helps speedup the operation.
        collect_levels = [i for i in range(self.num_levels - 1) if
                          kwargs["update_meta"][i]] + [self.num_levels - 1]

        # Get a batch.
        obs0, obs1, act, rew, done, additional = self.replay_buffer.sample(
            with_additional, collect_levels)

        # Do not use done masks for lower-level policies with negative
        # intrinsic rewards (these the policies to terminate early).
        if self._negative_reward_fn():
            for i in range(self.num_levels - 1):
                done[i+1] = np.array([False] * len(done[i+1]))

        # Loop through all meta-policies.
        for i in range(self.num_levels - 1):
            if kwargs['update_meta'][i] and not self._pretrain_level(i):
                # Replace the goals with the most likely goals.
                if self.off_policy_corrections and i == 0:  # FIXME
                    meta_act = self._sample_best_meta_action(
                        meta_obs0=obs0[i],
                        meta_obs1=obs1[i],
                        meta_action=act[i],
                        worker_obses=additional["worker_obses"],
                        worker_actions=additional["worker_actions"],
                        k=8
                    )
                    act[i] = meta_act

                if self.cooperative_gradients:
                    # Perform the cooperative gradients update procedure.
                    self._cooperative_gradients_update(
                        obs0=obs0,
                        actions=act,
                        rewards=rew,
                        obs1=obs1,
                        terminals1=done,
                        level_num=i,
                        update_actor=kwargs['update_meta_actor'],
                    )
                else:
                    # Perform the regular meta update procedure.
                    self.policy[i].update_from_batch(
                        obs0=obs0[i],
                        actions=act[i],
                        rewards=rew[i],
                        obs1=obs1[i],
                        terminals1=done[i],
                        update_actor=kwargs['update_meta_actor'],
                    )

        # Update the lowest level policy.
        self.policy[-1].update_from_batch(
            obs0=obs0[-1],
            actions=act[-1],
            rewards=rew[-1],
            obs1=obs1[-1],
            terminals1=done[-1],
            update_actor=update_actor,
        )

    def get_action(self, obs, context, apply_noise, random_actions, env_num=0):
        """See parent class."""
        # Increment the internal number of get_action calls.
        self._steps += 1

        # Loop through the policies in the hierarchy.
        for i in range(self.num_levels - 1):
            if self._update_meta(i, env_num):
                if self._pretrain_level(i):
                    # Sample goals randomly when performing pre-training.
                    self.meta_action[env_num][i] = np.array([
                        self.policy[i].ac_space.sample()])
                else:
                    context_i = context if i == 0 \
                        else self.meta_action[env_num][i - 1]

                    # Update the meta action based on the output from the
                    # policy if the time period requires is.
                    self.meta_action[env_num][i] = self.policy[i].get_action(
                        obs, context_i, apply_noise, random_actions)
            else:
                # Update the meta-action in accordance with a fixed transition
                # function.
                self.meta_action[env_num][i] = self.goal_transition_fn(
                    obs0=np.array(
                        [self._observations[env_num][-1][self.goal_indices]]),
                    goal=self.meta_action[env_num][i],
                    obs1=obs[:, self.goal_indices]
                )

        # Return the action to be performed within the environment (i.e. the
        # action by the lowest level policy).
        action = self.policy[-1].get_action(
            obs=obs,
            context=self.meta_action[env_num][-1],
            apply_noise=apply_noise,
            random_actions=random_actions and self.pretrain_path is None)

        return action

    def store_transition(self, obs0, context0, action, reward, obs1, context1,
                         done, is_final_step, env_num=0, evaluate=False):
        """See parent class."""
        # the time since the most recent sample began collecting step samples
        t_start = len(self._observations[env_num])

        # Flatten the observations.
        obs0 = obs0.flatten()
        obs1 = obs1.flatten()

        for i in range(1, self.num_levels):
            # Actions and intrinsic rewards for the high-level policies are
            # only updated when the action is recomputed by the graph.
            if self._update_meta(self.num_levels - i, env_num):
                self._rewards[env_num][-i].append(0)
                self._actions[env_num][-i-1].append(
                    self.meta_action[env_num][-i].flatten())

            # Compute the intrinsic rewards and append them to the list of
            # rewards.
            self._rewards[env_num][-i][-1] += \
                self.intrinsic_reward_scale[-i] * \
                self.intrinsic_reward_fn(
                    states=obs0,
                    goals=self.meta_action[env_num][-i].flatten(),
                    next_states=obs1
                )

        # The highest level policy receives the sum of environmental rewards.
        self._rewards[env_num][0][0] += reward

        # The lowest level policy's actions are received from the algorithm.
        self._actions[env_num][-1].append(action)

        # Add the environmental observations and contextual terms to their
        # respective lists.
        self._observations[env_num].append(obs0)
        if t_start == 0:
            self._contexts[env_num].append(context0)

        # Modify the done mask in accordance with the TD3 algorithm. Done masks
        # that correspond to the final step are set to False.
        self._dones[env_num].append(done and not is_final_step)

        # Add a sample to the replay buffer.
        if self._update_meta(0, env_num) or done:
            # Add the last observation and context.
            self._observations[env_num].append(obs1)
            self._contexts[env_num].append(context1)

            # Compute the current state goals to add to the final observation.
            for i in range(self.num_levels - 1):
                self._actions[env_num][i].append(self.goal_transition_fn(
                    obs0=obs0[self.goal_indices],
                    goal=self.meta_action[env_num][i],
                    obs1=obs1[self.goal_indices]
                ).flatten())

            # Avoid storing samples when performing evaluations.
            if not evaluate:
                if not self.hindsight \
                        or random.random() < self.subgoal_testing_rate:
                    # Store a sample in the replay buffer.
                    self.replay_buffer.add(
                        obs_t=self._observations[env_num],
                        context_t=self._contexts[env_num],
                        action_t=self._actions[env_num],
                        reward_t=self._rewards[env_num],
                        done_t=self._dones[env_num],
                    )

                if self.hindsight:
                    # Some temporary attributes.
                    worker_obses = [
                        self._get_obs(self._observations[env_num][i],
                                      self._actions[env_num][0][i], 0)
                        for i in range(len(self._observations[env_num]))]
                    intrinsic_rewards = self._rewards[env_num][-1]

                    # Implement hindsight action and goal transitions.
                    goal, rewards = self._hindsight_actions_goals(
                        initial_observations=worker_obses,
                        initial_rewards=intrinsic_rewards
                    )
                    new_actions = deepcopy(self._actions[env_num])
                    new_actions[0] = goal
                    new_rewards = deepcopy(self._rewards[env_num])
                    new_rewards[-1] = rewards

                    # Store the hindsight sample in the replay buffer.
                    self.replay_buffer.add(
                        obs_t=self._observations[env_num],
                        context_t=self._contexts[env_num],
                        action_t=new_actions,
                        reward_t=new_rewards,
                        done_t=self._dones[env_num],
                    )

            # Clear the memory that has been stored in the replay buffer.
            self.clear_memory(env_num)

    def _update_meta(self, level, env_num):
        """Determine whether a meta-policy should update its action.

        This is done by checking the length of the observation lists that are
        passed to the replay buffer, which are cleared whenever the highest
        level meta-period has been met or the environment has been reset.

        If the meta period is defined as a list, the period of level i (indexed
        from highest to lowest) is equal to the multiple of the elements in the
        list after index i.

        Parameters
        ----------
        level : int
            the level of the policy
        env_num : int
            the environment number. Used to handle situations when multiple
            parallel environments are being used.

        Returns
        -------
        bool
            True if the action should be updated by the meta-policy at the
            given level
        """
        # In the case of passing the lowest level policy, return True (always
        # perform an action).
        if level == self.num_levels - 1:
            return True

        # the time since the most recent sample began collecting step samples
        t_start = len(self._observations[env_num])

        # meta-action period of the given level
        if isinstance(self.meta_period, int):
            level_period = self.meta_period ** (self.num_levels - level - 1)
        else:
            level_period = reduce((lambda x, y: x*y), self.meta_period[level:])

        return t_start % level_period == 0

    def clear_memory(self, env_num):
        """Clear internal memory that is used by the replay buffer."""
        self._actions[env_num] = [[] for _ in range(self.num_levels)]
        self._rewards[env_num] = \
            [[0]] + [[] for _ in range(self.num_levels - 1)]
        self._observations[env_num] = []
        self._contexts[env_num] = []
        self._dones[env_num] = []

    def get_td_map(self):
        """See parent class."""
        # Not enough samples in the replay buffer.
        if not self.replay_buffer.can_sample():
            return {}

        # Get a batch.
        obs0, obs1, act, rew, done, _ = self.replay_buffer.sample(False)

        td_map = {}
        for i in range(self.num_levels):
            td_map.update(self.policy[i].get_td_map_from_batch(
                obs0=obs0[i],
                actions=act[i],
                rewards=rew[i],
                obs1=obs1[i],
                terminals1=done[i]
            ))

        return td_map

    def _negative_reward_fn(self):
        """Return True if the intrinsic reward returns negative values.

        Intrinsic reward functions with negative rewards incentivize early
        terminations, which we attempt to mitigate in the training operation by
        preventing early terminations from return an expected return of 0.
        """
        return "exp" not in self.intrinsic_reward_type \
            and "non" not in self.intrinsic_reward_type

    def _pretrain_level(self, level):
        """Check whether the current level should be training.

        When using `pretrain_worker` the lowest level policy is trained every
        step, and higher level policies are incrementally unfrozen for a
        fraction of the training steps. The highest level policy is not trained
        in this case, but the checkpoints can later be used to continue
        training the entire hierarchy.

        Parameters
        ----------
        level : int
            the level of the policy

        Returns
        -------
        bool
            True if the level should not be trained and should perform random
            actions, False otherwise
        """
        # number of steps to perform pretraining for a given level, assuming
        # pretrain_worker is set to True.
        pretrain_steps = self.total_steps * \
            (self.num_levels - level - 1) / (self.num_levels - 1)

        if level == 0:
            # bug fix for the final step
            return self.pretrain_worker
        else:
            return self.pretrain_worker and (self._steps < pretrain_steps)

    # ======================================================================= #
    #                       Auxiliary methods for HIRO                        #
    # ======================================================================= #

    def _sample_best_meta_action(self,
                                 meta_obs0,
                                 meta_obs1,
                                 meta_action,
                                 worker_obses,
                                 worker_actions,
                                 k=10):
        """Return meta-actions that approximately maximize low-level log-probs.

        Parameters
        ----------
        meta_obs0 : array_like
            (batch_size, m_obs_dim) matrix of meta observations
        meta_obs1 : array_like
            (batch_size, m_obs_dim) matrix of next time step meta observations
        meta_action : array_like
            (batch_size, m_ac_dim) matrix of meta actions
        worker_obses : array_like
            (batch_size, w_obs_dim, meta_period+1) matrix of current Worker
            state observations
        worker_actions : array_like
            (batch_size, w_ac_dim, meta_period) matrix of current Worker
            environmental actions
        k : int, optional
            number of goals returned, excluding the initial goal and the mean
            value

        Returns
        -------
        array_like
            (batch_size, m_ac_dim) matrix of most likely meta actions
        """
        batch_size, goal_dim = meta_action.shape

        # Collect several samples of potentially optimal goals.
        sampled_actions = self._sample(meta_obs0, meta_obs1, meta_action, k)
        assert sampled_actions.shape == (batch_size, goal_dim, k)

        # Compute the fitness of each candidate goal. The fitness is the sum of
        # the log-probabilities of each action for the given goal.
        fitness = self._log_probs(
            sampled_actions, worker_obses, worker_actions)
        assert fitness.shape == (batch_size, k)

        # For each sample, choose the meta action that maximizes the fitness.
        indx = np.argmax(fitness, 1)
        best_goals = np.asarray(
            [sampled_actions[i, :, indx[i]] for i in range(batch_size)])

        return best_goals

    def _sample(self, meta_obs0, meta_obs1, meta_action, num_samples, sc=0.5):
        """Sample different goals.

        The goals are sampled as follows:

        * The first num_samples-2 goals are acquired from a random Gaussian
          distribution centered at s_{t+c} - s_t.
        * The second to last goal is s_{t+c} - s_t.
        * The last goal is the originally sampled goal g_t.

        Parameters
        ----------
        meta_obs0 : array_like
            (batch_size, m_obs_dim) matrix of meta observations
        meta_obs1 : array_like
            (batch_size, m_obs_dim) matrix of next time step meta observations
        meta_action : array_like
            (batch_size, m_ac_dim) matrix of meta actions
        num_samples : int
            number of samples
        sc : float
            scaling factor for the normal distribution.

        Returns
        -------
        array_like
            (batch_size, goal_dim, num_samples) matrix of sampled goals

        Helps
        -----
        * _sample_best_meta_action(self)
        """
        batch_size, goal_dim = meta_action.shape
        goal_space = self.policy[0].ac_space
        spec_range = goal_space.high - goal_space.low
        random_samples = num_samples - 2

        # Compute the mean and std for the Gaussian distribution to sample
        # from, and well as the maxima and minima.
        loc = meta_obs1[:, self.goal_indices] - meta_obs0[:, self.goal_indices]
        scale = [sc * spec_range / 2]
        minimum, maximum = [goal_space.low], [goal_space.high]

        new_loc = np.zeros((batch_size, goal_dim, random_samples))
        new_scale = np.zeros((batch_size, goal_dim, random_samples))
        for i in range(random_samples):
            new_loc[:, :, i] = loc
            new_scale[:, :, i] = scale

        new_minimum = np.zeros((batch_size, goal_dim, num_samples))
        new_maximum = np.zeros((batch_size, goal_dim, num_samples))
        for i in range(num_samples):
            new_minimum[:, :, i] = minimum
            new_maximum[:, :, i] = maximum

        # Generate random samples for the above distribution.
        normal_samples = np.random.normal(
            size=(random_samples * batch_size * goal_dim))
        normal_samples = normal_samples.reshape(
            (batch_size, goal_dim, random_samples))

        samples = np.zeros((batch_size, goal_dim, num_samples))
        samples[:, :, :-2] = new_loc + normal_samples * new_scale
        samples[:, :, -2] = loc
        samples[:, :, -1] = meta_action

        # Clip the values based on the meta action space range.
        samples = np.minimum(np.maximum(samples, new_minimum), new_maximum)

        return samples

    def _log_probs(self, meta_actions, worker_obses, worker_actions):
        """Calculate the log probability of the next goal by the meta-policies.

        Parameters
        ----------
        meta_actions : array_like
            (batch_size, m_ac_dim, num_samples) matrix of candidate higher-
            level policy actions
        worker_obses : array_like
            (batch_size, w_obs_dim, meta_period + 1) matrix of lower-level
            policy observations
        worker_actions : array_like
            (batch_size, w_ac_dim, meta_period) list of lower-level policy
            actions

        Returns
        -------
        array_like
            (batch_size, num_samples) fitness associated with every state /
            action / goal pair

        Helps
        -----
        * _sample_best_meta_action(self):
        """
        raise NotImplementedError

    # ======================================================================= #
    #                       Auxiliary methods for HAC                         #
    # ======================================================================= #

    def _hindsight_actions_goals(self, initial_observations, initial_rewards):
        """Calculate hindsight goal and action transitions.

        These are then stored in the replay buffer along with the original
        (non-hindsight) sample.

        See the README at the front page of this repository for an in-depth
        description of this procedure.

        Parameters
        ----------
        initial_observations : array_like
            the original worker observations with the non-hindsight goals
            appended to them
        initial_rewards : array_like
            the original intrinsic rewards

        Returns
        -------
        array_like
            the goal at every step in hindsight
        array_like
            the modified intrinsic rewards taking into account the hindsight
            goals

        Helps
        -----
        * store_transition(self):
        """
        new_goals = []
        observations = deepcopy(initial_observations)
        rewards = deepcopy(initial_rewards)
        hindsight_goal = 0 if self.relative_goals \
            else observations[-1][self.goal_indices]
        obs_tp1 = observations[-1]

        for i in range(1, len(observations) + 1):
            obs_t = observations[-i]

            # Calculate the hindsight goal in using relative goals. If not, the
            # hindsight goal is simply a subset of the final state observation.
            if self.relative_goals:
                hindsight_goal += \
                    obs_tp1[self.goal_indices] - obs_t[self.goal_indices]

            # Modify the Worker intrinsic rewards based on the new hindsight
            # goal.
            if i > 1:
                # FIXME: intrinsic_reward_scale
                rewards[-(i - 1)] = self.intrinsic_reward_scale[0] \
                    * self.intrinsic_reward_fn(obs_t, hindsight_goal, obs_tp1)

            obs_tp1 = deepcopy(obs_t)
            new_goals = [deepcopy(hindsight_goal)] + new_goals

        return new_goals, rewards

    # ======================================================================= #
    #                       Auxiliary methods for CHER                        #
    # ======================================================================= #

    def _setup_cooperative_gradients(self):
        """Create the cooperative gradients meta-policy optimizer."""
        raise NotImplementedError

    def _cooperative_gradients_update(self,
                                      obs0,
                                      actions,
                                      rewards,
                                      obs1,
                                      terminals1,
                                      level_num,
                                      update_actor=True):
        """Perform the gradient update procedure for the CHER algorithm.

        This procedure is similar to update_from_batch, expect it runs the
        self.cg_optimizer operation instead of the policy object's optimizer,
        and utilizes some information from the worker samples as well.

        Parameters
        ----------
        obs0 : list of array_like
            (batch_size, obs_dim) matrix of observations for every level in the
            hierarchy
        actions : list of array_like
            (batch_size, ac_dim) matrix of actions for every level in the
            hierarchy
        obs1 : list of array_like
            (batch_size, obs_dim) matrix of next step observations for every
            level in the hierarchy
        rewards : list of array_like
            (batch_size,) vector of rewards for every level in the hierarchy
        terminals1 : list of numpy bool
            (batch_size,) vector of done masks for every level in the hierarchy
        level_num : int
            the hierarchy level number of the policy to optimize
        update_actor : bool
            specifies whether to update the actor policy of the meta policy.
            The critic policy is still updated if this value is set to False.

        Returns
        -------
        [float, float]
            meta-policy critic loss
        float
            meta-policy actor loss
        """
        raise NotImplementedError
