describe 'forecast_hours' do
  it 'gets a list of forecast hours' do
    output = run('forecast_hours')
    expect(output).to include('Available forecast hours:')
    expect(output).to match(/- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}: \d+(, \d+)*/)
  end

  it 'gets a list of forecast hours with an ensemble member' do
    output = run('forecast_hours', '--ens-member', '1')
    expect(output).to include('Available forecast hours:')
    expect(output).to match(/- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}: \d+(, \d+)*/)
  end

  it 'gets a list of forecast hours with intracycle' do
    output = run('forecast_hours', '--intracycle')
    expect(output).to include('Available forecast hours:')
    expect(output).to match(/- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}: \d+(, \d+)*/)
  end


end
