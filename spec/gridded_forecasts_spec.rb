describe 'gridded_forecasts' do

  let(:initialization_time) {
    init = (Time.now - 24 * 60 * 60)
    Time.new(init.year, init.month, init.day, init.hour - (init.hour % 6), 0, 0, 0)
  }

  let(:forecast_hour) { 24 }

  def sanitize(var)
    var.gsub('/', '_')
  end

  def expect_gridded_by_time(var, model: 'wm4')
    valid_at = (Time.now + 24 * 60 * 60)
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)

    output_path = "spec_outputs/gridded_forecast_#{sanitize(var)}.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('gridded', var, valid_at.strftime('%Y%m%d%H'), output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    # Valid time should be reasonably close to requested time
    diff_seconds = (details[:valid_at] - valid_at.utc).abs
    expect(diff_seconds).to be < 12 * 60 * 60

    raw = details[:raw]
    expect(raw).to include("latitude:")
    expect(raw).to include("longitude:")
    if var.include?('/')
      level_str, var_name = var.split('/', 2)
      expect(raw).to satisfy { |r| r.include?("#{var_name}:") || r.include?("#{var_name}_#{level_str}:") }
    else
      expect(raw).to include("#{var}:")
    end
  end

  it 'saves temperature_2m gridded forecast by time to netcdf' do
    expect_gridded_by_time('temperature_2m')
  end

  it 'saves wind_u_10m gridded forecast by time to netcdf' do
    expect_gridded_by_time('wind_u_10m')
  end

  it 'saves pressure_msl gridded forecast by time to netcdf' do
    expect_gridded_by_time('pressure_msl')
  end

  it 'saves 500/temperature gridded forecast by time to netcdf' do
    expect_gridded_by_time('500/temperature')
  end

  it 'saves 500/wind_u gridded forecast by time to netcdf' do
    expect_gridded_by_time('500/wind_u')
  end

  it 'supports level/variable syntax via the gridded command' do
    variable = '500/wind_v'
    model = 'wm4'

    output_path = "spec_outputs/gridded_forecast_#{sanitize(variable)}.nc"
    File.delete(output_path) if File.exist?(output_path)

    valid_at = (Time.now + 24 * 60 * 60)
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)
    run('gridded', variable, valid_at.strftime('%Y%m%d%H'), output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    diff_seconds = (details[:valid_at] - valid_at.utc).abs
    expect(diff_seconds).to be < 12 * 60 * 60
    raw = details[:raw]
    # For level variables, dataset often stores as var_level (e.g., wind_v_500)
    expect(raw).to satisfy { |r| r.include?('wind_v_500:') || r.include?('wind_v:') }
  end

  it 'supports variable level syntax via the gridded command' do
    variable = 'temperature'
    level = '500'
    model = 'wm4'

    output_path = "spec_outputs/gridded_forecast_#{sanitize(level + '/' + variable)}.nc"
    File.delete(output_path) if File.exist?(output_path)

    valid_at = (Time.now + 24 * 60 * 60)
    valid_at = Time.new(valid_at.year, valid_at.month, valid_at.day, valid_at.hour, 0, 0, valid_at.utc_offset)
    run('gridded', variable, level, valid_at.strftime('%Y%m%d%H'), output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    diff_seconds = (details[:valid_at] - valid_at.utc).abs
    expect(diff_seconds).to be < 12 * 60 * 60
    raw = details[:raw]
    expect(raw).to satisfy { |r| r.include?('temperature_500:') || r.include?('temperature:') }
  end

  it 'supports historical variable level syntax via the gridded command' do
    variable = 'temperature'
    level = '500'
    model = 'wm4'

    output_path = "spec_outputs/gridded_forecast_#{sanitize(level + '/' + variable)}_hist.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('gridded', variable, level, initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq((initialization_time.utc + forecast_hour * 60 * 60))
    raw = details[:raw]
    expect(raw).to satisfy { |r| r.include?('temperature_500:') || r.include?('temperature:') }
  end

  it 'saves full gridded forecasts (all variables) to netcdf' do
    model = 'wm4'

    output_path = 'spec_outputs/gridded_forecast_all.nc'
    File.delete(output_path) if File.exist?(output_path)

    run('gridded', 'all', initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq((initialization_time.utc + forecast_hour * 60 * 60))

    raw = details[:raw]
    # spot-check a few expected variables present in FULL/all dataset
    expect(raw).to include('temperature_2m:')
    expect(raw).to include('wind_u_10m:')
    expect(raw).to include('pressure_msl:')
  end

  it 'can get a historical gridded forecast using initialization_time and forecast_hour' do
    variable = 'temperature_2m'
    model = 'wm4'

    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('gridded', variable, initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq((initialization_time.utc + forecast_hour * 60 * 60))
    expect(details[:raw]).to include('temperature_2m:')
  end

  it 'can get the ensemble mean gridded forecast for a specific initialization time' do
    variable = 'temperature_2m'
    model = 'wm4-ens'
    output_path = "spec_outputs/gridded_forecast_#{variable}_#{initialization_time.strftime('%Y%m%d%H')}_ens_mean.nc"
    File.delete(output_path) if File.exist?(output_path)

    run('gridded', variable, initialization_time.strftime('%Y%m%d%H'), forecast_hour.to_s, output_path, '-e', 'mean', '-m', model)
    expect(File.exist?(output_path)).to be true

    details = netcdf_meta(output_path)
    expect(details[:initialization_time]).to eq(initialization_time.utc)
    expect(details[:forecast_hour]).to eq(forecast_hour)
    expect(details[:valid_at]).to eq(initialization_time.utc + forecast_hour * 60 * 60)
    expect(details[:raw]).to include('temperature_2m:')
  end

end
