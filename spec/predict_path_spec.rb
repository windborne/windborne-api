describe 'predict-path' do

  it 'saves predicted path to a JSON file when an output path is provided' do
    mission_id = sample_mission_id
    skip 'No flying missions available to test predict-path' unless mission_id

    out_path = 'spec_outputs/predicted_path.json'
    output = run('predict-path', mission_id, out_path)

    expect(output).to_not include('Traceback')

    expect(File.exist?(out_path)).to be true

    data = JSON.parse(File.read(out_path))
    expect([Hash, Array]).to include(data.class)
  end
end


