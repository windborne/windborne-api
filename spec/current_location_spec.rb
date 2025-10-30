describe 'current-location' do

  it 'prints the current location for a flying mission' do
    mission_id = sample_mission_id
    skip 'No flying missions available to test current-location' unless mission_id

    output = run('current-location', mission_id)
    if output.include?("Our server couldn't find") || output.include?('No mission found')
      skip 'Selected mission has no current-location data'
    end

    expect(output).not_to include('Traceback')
    expect(output).to include('Current location')
    expect(output).to match(/^Latitude\s+Longitude\s+Altitude\s*$/)
  end

  it 'saves current location to a JSON file when an output path is provided' do
    mission_id = sample_mission_id
    skip 'No flying missions available to test current-location saving' unless mission_id

    out_path = 'spec_outputs/current_location.json'
    output = run('current-location', mission_id, out_path)
    expect(output).not_to include('Traceback')
    
    if !output.include?("Saved to #{out_path}")
      skip 'Selected mission has no current-location data'
    end

    expect(File.exist?(out_path)).to be true

    body = JSON.parse(File.read(out_path))
    expect(body).to be_a(Hash)
    expect(body).to have_key('latitude')
    expect(body).to have_key('longitude')
  end
end


