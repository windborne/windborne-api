describe 'point_forecasts' do
  it 'generates forecasts for a single location' do
    output = run('points', '37.7749,-122.4194')
    expect(output).to include('Forecast for (37.7749, -122.4194)')
  end

  it 'generates forecasts for multiple locations' do
    locations = %w[
      37.7749,-122.4194
      34.0522,-118.2437
      40.7128,-74.0060
    ]

    output = run('points', locations.join(';'))
    locations.each do |location|
      expect(output).to include("Forecast for (#{location.split(',').join(', ')})")
    end
  end

  it 'can save to csv' do
    require 'csv'

    output_path = 'spec_outputs/point_forecasts.csv'
    File.delete(output_path) if File.exist?(output_path)
    run('points', '37.7749,-122.4194', output_path)

    expect(File.exist?(output_path)).to be true
    csv_data = CSV.read(output_path, headers: true)
    expect(csv_data.size).to be > 10
  end
end