describe 'gridded_forecasts' do
  it 'saves gridded forecasts to netcdf' do
    variables = %w[
      temp_2m
      dewpoint_2m
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

      details = netcdf_meta(output_path)
      expect(details[:valid_at]).to eq(valid_at.utc)
    end
  end

  it 'saves full gridded forecasts to netcdf' do
    valid_at = (Time.now + 24 * 60 * 60).utc
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    output_path = 'spec_outputs/gridded_forecast_full.nc'
    File.delete(output_path) if File.exist?(output_path)
    run('grid_full', valid_at.strftime('%Y%m%d%H'), output_path, print: true)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:valid_at]).to eq(valid_at.utc)
  end

  it 'can get a gridded forecast for a specific initialization time' do
    variable = 'temp_2m'

    # set initialization time to 24 hours ago
    # make sure the hour is divisible by 6
    initialization_time = (Time.now - 24 * 60 * 60).utc
    initialization_time = Time.new(initialization_time.year, initialization_time.month, initialization_time.day, initialization_time.hour - (initialization_time.hour % 6), 0, 0, initialization_time.utc_offset)
    forecast_hour = 24

    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('hist_temp_2m', initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, print: true)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
  end
end
