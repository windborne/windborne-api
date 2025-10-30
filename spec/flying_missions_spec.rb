describe 'flying-missions' do
  it 'prints currently flying missions or a helpful message' do
    output = run('flying-missions')

    expect(output).not_to include('Traceback')
    expect(output).to satisfy { |o|
      o.include?('Currently flying missions:') ||
      o.include?('No missions are currently flying.')
    }
  end

  it 'saves missions to a JSON file when an output path is provided' do
    out_path = 'spec_outputs/flying_missions.json'
    output = run('flying-missions', out_path)

    expect(output).to include("Saved to #{out_path}")
    expect(File.exist?(out_path)).to be true

    body = JSON.parse(File.read(out_path))
    expect(body).to be_a(Hash)
    expect(body).to have_key('missions')
    expect(body['missions']).to be_a(Array)
  end
end
