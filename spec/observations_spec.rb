describe 'observations' do

  it 'fetches observations to a file' do
    output_path = 'spec_outputs/observations_dec_2024.json'
    File.delete(output_path) if File.exist?(output_path)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path)

    observations = JSON.parse(File.read(output_path))
    expect(observations.size).to eq(7950)
  end

  it 'fetches observations to a file with a mission filter' do
    output_path = 'spec_outputs/observations_dec_2024_1960.json'
    File.delete(output_path) if File.exist?(output_path)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path, '-m', 'e58f5b18-de55-4bf4-8a62-d840651441f4')

    observations = JSON.parse(File.read(output_path))
    expect(observations.size).to eq(360)
  end

  it 'fetches observations to a directory' do
    output_dir = 'spec_outputs/dec_2024'
    FileUtils.rm_rf(output_dir) if File.exist?(output_dir)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", "json", "-d", output_dir)

    json_outputs = Dir.glob("#{output_dir}/*.json")
    expect(json_outputs.size).to eq(24)
    total_observations = json_outputs.map { |file| JSON.parse(File.read(file)).size }.sum
    expect(total_observations).to eq(7950)

    w1958_obs = JSON.parse(File.read("#{output_dir}/WindBorne_W-1958_2024-12-01_06_6h.json"))
    expect(w1958_obs.size).to eq(67)
  end

  it 'fetches observations to a directory with lower bucket number' do
    output_dir = 'spec_outputs/dec_2024_2h_buckets'
    FileUtils.rm_rf(output_dir) if File.exist?(output_dir)
    run('observations', "2024-12-01_06:00", "2024-12-01_12:00", "json", "-d", output_dir, '-b', '2')

    json_outputs = Dir.glob("#{output_dir}/*.json")
    expect(json_outputs.size).to eq(70)
    total_observations = json_outputs.map { |file| JSON.parse(File.read(file)).size }.sum
    expect(total_observations).to eq(47014)

    w1958_obs = JSON.parse(File.read("#{output_dir}/WindBorne_W-1958_2024-12-01_06_2h.json"))
    expect(w1958_obs.size).to eq(67)

    min_timestamp = 1733032800
    max_timestamp = 1733040000

    w1958_obs.each do |observation|
      timestamp = observation['timestamp']
      expect(timestamp).to be >= min_timestamp
      expect(timestamp).to be <= max_timestamp
    end
  end

  it 'fetches observations to csv' do
    require 'csv'

    output_path = 'spec_outputs/observations_dec_2024_1960.csv'
    File.delete(output_path) if File.exist?(output_path)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path, '-m', 'e58f5b18-de55-4bf4-8a62-d840651441f4')

    csv = CSV.read(output_path)
    expect(csv.size).to eq(361)
  end

  it 'fetches observations to netcdf' do
    output_path = 'spec_outputs/observations_dec_2024_1960.nc'
    File.delete(output_path) if File.exist?(output_path)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path, '-m', 'e58f5b18-de55-4bf4-8a62-d840651441f4')

    expect(File.exist?(output_path)).to be true

    # inject a python script to check the netcdf file
    python_script = "from netCDF4 import Dataset; f = Dataset('#{output_path}', 'r'); print(f); print('\\n'.join(name + ': ' + str(var[0]) for name, var in f.variables.items()))"
    details, _ = Open3.capture2("python3", "-c", python_script)

    expect(details).to include("flight_id: W-1960")
    expect(details).to include("dimensions(sizes): obs(360), time(360)")
    expect(details).to include("altitude: 14238.34")
    expect(details).to include("id: 44321883370")
    expect(details).to include("lat: 29.39379")
    expect(details).to include("lon: -13.585162")
    expect(details).to include("mission_id: e58f5b18-de55-4bf4-8a62-d840651441f4")
    expect(details).to include("mission_name: W-1960")
    expect(details).to include("air_pressure: 140.47")
    expect(details).to include("specific_humidity: --")
    expect(details).to include("speed_u: 33.86")
    expect(details).to include("speed_v: 4.11")
    expect(details).to include("air_temperature: --")
    expect(details).to include("obs: 0")
    expect(details).to include("humidity_mixing_ratio: --")
    expect(details).to include("wind_speed: 34.1085")
    expect(details).to include("wind_direction: 263.0791")
    expect(details).to include("time: 1733032805.0")
  end

  it 'fetches observations to little r' do
    output_path = 'spec_outputs/observations_dec_2024_1960.little_r'
    File.delete(output_path) if File.exist?(output_path)
    run('observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path, '-m', 'e58f5b18-de55-4bf4-8a62-d840651441f4')

    little_r = File.readlines(output_path)
    little_r << ' ' # add a newline at the end cause File.readlines does not include it (a bit weird but I've verified manually)
    expect(little_r.size).to eq(5*360)

    360.times do |obs_number|
      expect(little_r[obs_number * 5 + 0].size).to eq(621)
      expect(little_r[obs_number * 5 + 1].size).to eq(201)
      expect(little_r[obs_number * 5 + 2].size).to eq(201)
      expect(little_r[obs_number * 5 + 3].size).to eq(22)
      expect(little_r[obs_number * 5 + 4].size).to eq(1)
    end
  end

end
