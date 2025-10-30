describe 'launch-site' do
  let(:mission_id) { '494f8cb2-5fed-4c81-b3c4-5eacaa2ba4e0' }

  it 'prints the mission launch site details' do
    output = run('launch-site', mission_id)

    expect(output).not_to include('Traceback')
    expect(output).to include('Mission launch site')
    expect(output).to match(/^ID\s+/)
    expect(output).to match(/^Latitude\s+/)
    expect(output).to match(/^Longitude\s+/)
  end

  it 'saves launch site to a JSON file when an output path is provided' do
    out_path = 'spec_outputs/launch_site.json'
    output = run('launch-site', mission_id, out_path)

    expect(output).to include("Saved to #{out_path}")
    expect(File.exist?(out_path)).to be true

    body = JSON.parse(File.read(out_path))
    expect(body).to be_a(Hash)
    expect(body).to have_key('launch_site')
    expect(body['launch_site']).to be_a(Hash)
    expect(body['launch_site']).to have_key('id')
  end
end


