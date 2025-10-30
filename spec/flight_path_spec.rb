describe 'flight-path' do

  it 'prints the flight path table' do
    mission_id = sample_mission_id
    skip 'No flying missions available to test flight-path' unless mission_id

    output = run('flight-path', mission_id)

    expect(output).not_to include('Traceback')
    expect(output).not_to include("Our server couldn't find")
    expect(output).to include('Flight path')
    expect(output).to match(/^Time\s+Latitude\s+Longitude\s+Altitude\s*$/)
  end

  it 'saves flight path to a JSON file when an output path is provided' do
    mission_id = sample_mission_id
    skip 'No flying missions available to test flight-path saving' unless mission_id

    out_path = 'spec_outputs/flight_path.json'
    output = run('flight-path', mission_id, out_path)
    expect(output).not_to include('Traceback')
    expect(File.exist?(out_path)).to be true

    data = JSON.parse(File.read(out_path))
    # Expect format: { "<mission_id>": [ points... ] }
    expect(data).to be_a(Hash)
    points = data.values.first || []
    expect(points).to be_a(Array)
    expect(points.length).to be > 0
  end
end



