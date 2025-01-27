describe 'super_observations' do

  it 'fetches super_observations to a file' do
    output_path = 'spec_outputs/super_observations_dec_2024.json'
    File.delete(output_path) if File.exist?(output_path)
    run('super-observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path)

    super_observations = JSON.parse(File.read(output_path))
    expect(super_observations.size).to eq(356)
  end

  it 'fetches super observations to a file with a mission filter' do
    output_path = 'spec_outputs/super_observations_dec_2024_1960.json'
    File.delete(output_path) if File.exist?(output_path)
    run('super-observations', "2024-12-01_06:00", "2024-12-01_07:00", output_path, '-m', 'e58f5b18-de55-4bf4-8a62-d840651441f4')

    super_observations = JSON.parse(File.read(output_path))
    expect(super_observations.size).to eq(3)
  end

  it 'fetches super observations to a directory' do
    output_dir = 'spec_outputs/super_obs_dec_2024'
    FileUtils.rm_rf(output_dir) if File.exist?(output_dir)
    run('super-observations', "2024-12-01_06:00", "2024-12-01_07:00", "json", "-d", output_dir)

    json_outputs = Dir.glob("#{output_dir}/*.json")
    expect(json_outputs.size).to eq(23)
    total_super_observations = json_outputs.map { |file| JSON.parse(File.read(file)).size }.sum
    expect(total_super_observations).to eq(356)

    w1958_obs = JSON.parse(File.read("#{output_dir}/WindBorne_W-1958_2024-12-01_06_6h.json"))
    expect(w1958_obs.size).to eq(1)
  end

end
