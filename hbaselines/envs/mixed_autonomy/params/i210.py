"""I-210 subnetwork example."""
import os

from flow.controllers import RLController
from flow.controllers import IDMController
from flow.controllers import SimLaneChangeController
from flow.core.params import EnvParams
from flow.core.params import NetParams
from flow.core.params import InitialConfig
from flow.core.params import InFlows
from flow.core.params import VehicleParams
from flow.core.params import SumoParams
from flow.core.params import SumoLaneChangeParams
from flow.core.params import SumoCarFollowingParams
from flow.networks.i210_subnetwork import I210SubNetwork, EDGES_DISTRIBUTION
import flow.config as flow_config

from hbaselines.envs.mixed_autonomy.envs import AVOpenEnv
from hbaselines.envs.mixed_autonomy.envs import AVOpenMultiAgentEnv
import hbaselines.config as hbaselines_config

# the inflow rate of vehicles (in veh/hr)
INFLOW_RATE = 2050
# the speed of inflowing vehicles from the main edge (in m/s)
INFLOW_SPEED = 25.5
# fraction of vehicles that are RL vehicles. 0.10 corresponds to 10%
PENETRATION_RATE = 1/22
# horizon over which to run the env
HORIZON = 1500
# range for the inflows allowed in the network. If set to None, the inflows are
# not modified from their initial value.
INFLOWS = [1000, 2000]
# the path to the warmup files to initialize a network
WARMUP_PATH = os.path.join(
    hbaselines_config.PROJECT_PATH, "experiments/warmup/i210")


def get_flow_params(fixed_boundary,
                    stopping_penalty,
                    acceleration_penalty,
                    use_follower_stopper,
                    evaluate=False,
                    multiagent=False):
    """Return the flow-specific parameters of the I-210 subnetwork.

    Parameters
    ----------
    fixed_boundary : bool
        specifies whether the boundary conditions update in between resets
    stopping_penalty : bool
        whether to include a stopping penalty
    acceleration_penalty : bool
        whether to include a regularizing penalty for accelerations by the AVs
    use_follower_stopper : bool
        whether to use the follower-stopper controller for the AVs
    evaluate : bool
        whether to compute the evaluation reward
    multiagent : bool
        whether the automated vehicles are via a single-agent policy or a
        shared multi-agent policy with the actions of individual vehicles
        assigned by a separate policy call

    Returns
    -------
    dict
        flow-related parameters, consisting of the following keys:

        * exp_tag: name of the experiment
        * env_name: environment class of the flow environment the experiment
          is running on. (note: must be in an importable module.)
        * network: network class the experiment uses.
        * simulator: simulator that is used by the experiment (e.g. aimsun)
        * sim: simulation-related parameters (see flow.core.params.SimParams)
        * env: environment related parameters (see flow.core.params.EnvParams)
        * net: network-related parameters (see flow.core.params.NetParams and
          the network's documentation or ADDITIONAL_NET_PARAMS component)
        * veh: vehicles to be placed in the network at the start of a rollout
          (see flow.core.params.VehicleParams)
        * initial (optional): parameters affecting the positioning of vehicles
          upon initialization/reset (see flow.core.params.InitialConfig)
        * tls (optional): traffic lights to be introduced to specific nodes
          (see flow.core.params.TrafficLightParams)
    """
    # steps to run before the agent is allowed to take control (set to lower
    # value during testing)
    if WARMUP_PATH is not None:
        warmup_steps = 0
    else:
        warmup_steps = 50 if os.environ.get("TEST_FLAG") else 500

    # Create the base vehicle types that will be used for inflows.
    vehicles = VehicleParams()
    vehicles.add(
        "human",
        num_vehicles=0,
        acceleration_controller=(IDMController, {
            "a": 1.3,
            "b": 2.0,
            "noise": 0.3 if evaluate else 0.0,
            "display_warnings": False,
            "fail_safe": [
                "obey_speed_limit", "safe_velocity", "feasible_accel"],
        }),
        lane_change_controller=(SimLaneChangeController, {}),
        car_following_params=SumoCarFollowingParams(
            min_gap=0.5,
            # right of way at intersections + obey limits on deceleration
            speed_mode=12
        ),
        lane_change_params=SumoLaneChangeParams(
            lane_change_mode="sumo_default",
        ),
    )
    vehicles.add(
        "rl",
        num_vehicles=0,
        acceleration_controller=(RLController, {
            "fail_safe": [
                "obey_speed_limit", "safe_velocity", "feasible_accel"],
        }),
        car_following_params=SumoCarFollowingParams(
            min_gap=0.5,
            # right of way at intersections + obey limits on deceleration
            speed_mode=12,
        ),
        lane_change_params=SumoLaneChangeParams(
            lane_change_mode=0,  # no lane changes
        ),
    )

    # Add the inflows from the main highway.
    inflow = InFlows()
    inflow.add(
        veh_type="human",
        edge="ghost0",
        vehs_per_hour=INFLOW_RATE * 5 * (1 - PENETRATION_RATE),
        depart_lane="best",
        depart_speed=25.5)
    inflow.add(
        veh_type="rl",
        edge="ghost0",
        vehs_per_hour=INFLOW_RATE * 5 * PENETRATION_RATE,
        depart_lane="best",
        depart_speed=25.5)

    return dict(
        # name of the experiment
        exp_tag="I-210_subnetwork",

        # name of the flow environment the experiment is running on
        env_name=AVOpenMultiAgentEnv if multiagent else AVOpenEnv,

        # name of the network class the experiment is running on
        network=I210SubNetwork,

        # simulator that is used by the experiment
        simulator="traci",

        # simulation-related parameters
        sim=SumoParams(
            sim_step=0.4,
            render=False,
            restart_instance=True,
            use_ballistic=True,
        ),

        # environment related parameters (see flow.core.params.EnvParams)
        env=EnvParams(
            evaluate=evaluate,
            horizon=HORIZON,
            warmup_steps=warmup_steps,
            done_at_exit=False,
            sims_per_step=1,
            additional_params={
                "max_accel": 0.5,
                "stopping_penalty": stopping_penalty,
                "acceleration_penalty": acceleration_penalty,
                "use_follower_stopper": use_follower_stopper,
                "obs_frames": 5,
                "inflows": None if fixed_boundary else INFLOWS,
                "rl_penetration": PENETRATION_RATE,
                "num_rl": float("inf") if multiagent else 25,
                "control_range": [573.08, 2363.27],
                "expert_model": (IDMController, {
                    "a": 1.3,
                    "b": 2.0,
                }),
                "warmup_path": WARMUP_PATH,
            }
        ),

        # network-related parameters (see flow.core.params.NetParams and the
        # network's documentation or ADDITIONAL_NET_PARAMS component)
        net=NetParams(
            inflows=inflow,
            template=os.path.join(
                flow_config.PROJECT_PATH,
                "examples/exp_configs/templates/sumo/i210_with_ghost_cell_"
                "with_downstream.xml"
            ),
            additional_params={
                "on_ramp": False,
                "ghost_edge": True,
            }
        ),

        # vehicles to be placed in the network at the start of a rollout (see
        # flow.core.params.VehicleParams)
        veh=vehicles,

        # parameters specifying the positioning of vehicles upon init / reset
        # (see flow.core.params.InitialConfig)
        initial=InitialConfig(
            edges_distribution=EDGES_DISTRIBUTION.copy(),
        ),
    )
