import os
from simulator.aircraft_simulator import AircraftSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "simulated")
    os.makedirs(output_dir, exist_ok=True)
    
    sim = AircraftSimulator(asset_id="AI101", asset_type="aircraft", seed=42)
    
    # Generate normal aircraft approach trajectory
    normal_df = sim.generate_approach_trajectory(duration_sec=120, dt_sec=1.0, add_noise=True)
    normal_path = os.path.join(output_dir, "aircraft_normal.csv")
    normal_df.to_csv(normal_path, index=False)
    print(f"Generated normal trajectory: {normal_path} ({len(normal_df)} rows)")
    
    # Generate sudden jump spoofing trajectory
    jump_df = SpoofingScenarioGenerator.inject_sudden_jump(normal_df, start_time_sec=40.0, end_time_sec=70.0)
    jump_path = os.path.join(output_dir, "aircraft_sudden_jump.csv")
    jump_df.to_csv(jump_path, index=False)
    print(f"Generated sudden jump spoofing trajectory: {jump_path} ({len(jump_df)} rows)")


if __name__ == "__main__":
    main()
