describe 'gridded_forecasts' do

  let(:initialization_time) {
    initialization_time = (Time.now - 24 * 60 * 60).utc
    initialization_time = Time.new(initialization_time.year, initialization_time.month, initialization_time.day, initialization_time.hour - (initialization_time.hour % 6), 0, 0, initialization_time.utc_offset)
    initialization_time
  }

  let(:forecast_hour) { 24 }
  let(:variable) { 'temp_2m' }

  it 'saves gridded forecasts to netcdf' do
    variables = %w[
      temp_2m
      dewpoint_2m
      wind_u_10m
      wind_v_10m
      pressure_msl
      500hpa_temperature
      850hpa_temperature
      500hpa_wind_u
      500hpa_wind_v
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

  it 'can use the generic gridded command' do
    variable = '500/wind_u'

    valid_at = (Time.now + 24 * 60 * 60).utc
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    output_path = "spec_outputs/gridded_forecast_wind_u_500hpa.nc"
    File.delete(output_path) if File.exist?(output_path)
    run('gridded', variable, valid_at.strftime('%Y%m%d%H'), output_path)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:valid_at]).to eq(valid_at.utc)
  end

  it 'saves full gridded forecasts to netcdf' do
    valid_at = (Time.now + 24 * 60 * 60).utc
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    output_path = 'spec_outputs/gridded_forecast_full.nc'
    File.delete(output_path) if File.exist?(output_path)
    run('grid_full', valid_at.strftime('%Y%m%d%H'), output_path)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:valid_at]).to eq(valid_at.utc)
  end

  it 'can use the generic hist_gridded command to get a historical gridded forecast' do
    variable = '500/wind_v'
    initialization_time = (Time.now - 24 * 60 * 60).utc
    initialization_time = Time.new(initialization_time.year, initialization_time.month, initialization_time.day, initialization_time.hour - (initialization_time.hour % 6), 0, 0, initialization_time.utc_offset)
    forecast_hour = 24
    
    output_path = "spec_outputs/gridded_forecast_wind_u_500hpa_#{initialization_time.strftime('%Y%m%d%H')}.nc"
    File.delete(output_path) if File.exist?(output_path)
    run('hist_gridded', variable, initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
  end

  it 'can get a gridded forecast for a specific initialization time' do
    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('hist_temp_2m', initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
  end

  it 'can get the ensemble mean gridded forecast for a specific initialization time' do
    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}_ens_mean.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('hist_temp_2m', initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '--ens-member', 'mean')
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
    expect(details[:raw]).to include('WeatherMesh:ens:mean')
  end

  it 'can get the intracycle gridded forecast for a specific initialization time' do
    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}_intracycle.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('hist_temp_2m', initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '--intracycle')
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
    expect(details[:raw]).to include('WeatherMesh:intracycle')
  end


end
