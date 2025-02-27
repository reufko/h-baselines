"""SAC-compatible multi-agent goal-conditioned hierarchical policy."""
from hbaselines.multiagent.base import MultiAgentPolicy as BasePolicy
from hbaselines.goal_conditioned.sac import GoalConditionedPolicy


class MultiGoalConditionedPolicy(BasePolicy):
    """SAC-compatible multi-agent goal-conditioned hierarchical policy."""

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
                 target_entropy,
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
                 shared,
                 maddpg,
                 n_agents,
                 env_name="",
                 num_envs=1,
                 all_ob_space=None,
                 scope=None):
        """Instantiate a multi-agent feed-forward neural network policy.

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
        l2_penalty : float
            L2 regularization penalty. This is applied to the policy network.
        model_params : dict
            dictionary of model-specific parameters. See parent class.
        target_entropy : float
            target entropy used when learning the entropy coefficient. If set
            to None, a heuristic value is used.
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
        intrinsic_reward_scale : [float]
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
            Actions by the high-level policy are randomly sampled from its
            action space.
        pretrain_path : str or None
            path to the pre-trained worker policy checkpoints
        pretrain_ckpt : int or None
            checkpoint number to use within the worker policy path. If set to
            None, the most recent checkpoint is used.
        total_steps : int
            Total number of timesteps used during training. Used by a subset of
            algorithms.
        shared : bool
            whether to use a shared policy for all agents
        maddpg : bool
            whether to use an algorithm-specific variant of the MADDPG
            algorithm
        all_ob_space : gym.spaces.*
            the observation space of the full state space. Used by MADDPG
            variants of the policy.
        n_agents : int
            the expected number of agents in the environment. Only relevant if
            using shared policies with MADDPG or goal-conditioned hierarchies.
        scope : str
            an upper-level scope term. Used by policies that call this one.
        """
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr
        self.tau = tau
        self.gamma = gamma
        self.use_huber = use_huber

        super(MultiGoalConditionedPolicy, self).__init__(
            sess=sess,
            ob_space=ob_space,
            ac_space=ac_space,
            co_space=co_space,
            verbose=verbose,
            l2_penalty=l2_penalty,
            model_params=model_params,
            shared=shared,
            maddpg=maddpg,
            all_ob_space=all_ob_space,
            n_agents=n_agents,
            base_policy=GoalConditionedPolicy,
            num_envs=num_envs,
            scope=scope,
            additional_params=dict(
                buffer_size=buffer_size,
                batch_size=batch_size,
                actor_lr=actor_lr,
                critic_lr=critic_lr,
                tau=tau,
                gamma=gamma,
                use_huber=use_huber,
                target_entropy=target_entropy,
                num_levels=num_levels,
                meta_period=meta_period,
                intrinsic_reward_type=intrinsic_reward_type,
                intrinsic_reward_scale=intrinsic_reward_scale,
                relative_goals=relative_goals,
                off_policy_corrections=off_policy_corrections,
                hindsight=hindsight,
                subgoal_testing_rate=subgoal_testing_rate,
                cooperative_gradients=cooperative_gradients,
                cg_weights=cg_weights,
                cg_delta=cg_delta,
                pretrain_worker=pretrain_worker,
                pretrain_path=pretrain_path,
                pretrain_ckpt=pretrain_ckpt,
                total_steps=total_steps,
                env_name=env_name,
            ),
        )

    def _setup_maddpg(self, scope):
        """See setup."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")

    def _initialize_maddpg(self):
        """See initialize."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")

    def _update_maddpg(self, update_actor=True, **kwargs):
        """See update."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")

    def _get_action_maddpg(self,
                           obs,
                           context,
                           apply_noise,
                           random_actions,
                           env_num):
        """See get_action."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")

    def _store_transition_maddpg(self,
                                 obs0,
                                 context0,
                                 action,
                                 reward,
                                 obs1,
                                 context1,
                                 done,
                                 is_final_step,
                                 all_obs0,
                                 all_obs1,
                                 env_num,
                                 evaluate):
        """See store_transition."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")

    def _get_td_map_maddpg(self):
        """See get_td_map."""
        raise NotImplementedError(
            "This policy does not support MADDPG-variants of the training "
            "operation.")
