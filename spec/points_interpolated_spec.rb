describe 'points_interpolated' do
  it 'prints interpolated forecast for a single point' do
    output = run('points_interpolated', '--model', 'wm4', '40.7,-74.0')
    expect(output).to include('Generating interpolated point forecast...')
    expect(output).to include('Forecast for (40.7, -74.0)')
    expect(output).to include('Time')
    expect(output.split("\n").size).to be > 4
  end

  it 'prints interpolated forecast for multiple points' do
    output = run('points_interpolated', '--model', 'wm4', '40.7,-74.0;34.0,-118.2')
    expect(output).to include('Forecast for (40.7, -74.0)')
    expect(output).to include('Forecast for (34.0, -118.2)')
  end
end


