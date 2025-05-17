require 'open3'

def netcdf_details(output_path)
  python_script = "from netCDF4 import Dataset; f = Dataset('#{output_path}', 'r'); print(f); print('\\n'.join(name + ': ' + str(var[0]) for name, var in f.variables.items()))"
  details, _ = Open3.capture2("python3", "-c", python_script)

  details
end

def netcdf_meta(output_path)
  details = netcdf_details(output_path)

  initialization_time_raw = details.match(/initialization_time: (.+)/)[1] # iso string
  initialization_time = Time.parse(initialization_time_raw)
  forecast_hour = details.match(/forecast_hour: (.+)/)[1]&.to_i
  valid_at = initialization_time + forecast_hour.to_i * 60 * 60

  {
    initialization_time: initialization_time.utc,
    forecast_hour: forecast_hour,
    valid_at: valid_at.utc,
    details: details
  }
end
