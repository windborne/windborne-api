describe 'gridded_forecasts' do
  it 'saves gridded forecasts to netcdf' do
    variables = %w[
      temp_2m
      wind_u_10m
      wind_v_10m
      pressure_msl
      500hpa_temperature
      850hpa_temperature
    ]

    # valid_at should be 24 hours from now with the minutes and seconds set to 0
    valid_at = (Time.now + 24 * 60 * 60).utc
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    variables.each do |variable|
      output_path = "spec_outputs/gridded_forecast_#{variable}.nc"
      File.delete(output_path) if File.exist?(output_path)

      run("grid_#{variable}", valid_at.strftime('%Y%m%d%H'), output_path)
      expect(File.exist?(output_path)).to be true

      # inject a python script to check the netcdf file
      python_script = "from netCDF4 import Dataset; f = Dataset('#{output_path}', 'r'); print(f); print('\\n'.join(name + ': ' + str(var[0]) for name, var in f.variables.items()))"
      details, _ = Open3.capture2("python3", "-c", python_script)

      initialization_time = details.match(/initialization_time: (.+)/)[1] # iso string
      forecast_hour = details.match(/forecast_hour: (.+)/)[1]
      derived_valid_at = Time.parse(initialization_time) + forecast_hour.to_i * 60 * 60

      expect(derived_valid_at.utc).to eq(valid_at.utc)
    end
  end

  it 'saves full gridded forecasts to netcdf', focus: true do
    valid_at = (Time.now + 24 * 60 * 60).utc
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    output_path = 'spec_outputs/gridded_forecast_full.nc'
    File.delete(output_path) if File.exist?(output_path)
    run('grid_full', valid_at.strftime('%Y%m%d%H'), output_path, print: true)
    expect(File.exist?(output_path)).to be true

    python_script = "from netCDF4 import Dataset; f = Dataset('#{output_path}', 'r'); print(f); print('\\n'.join(name + ': ' + str(var[0]) for name, var in f.variables.items()))"
    details, _ = Open3.capture2("python3", "-c", python_script)

    initialization_time = details.match(/initialization_time: (.+)/)[1] # iso string
    forecast_hour = details.match(/forecast_hour: (.+)/)[1]
    derived_valid_at = Time.parse(initialization_time) + forecast_hour.to_i * 60 * 60

    expect(derived_valid_at.utc).to eq(valid_at.utc)
  end
end
