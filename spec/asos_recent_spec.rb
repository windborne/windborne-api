describe 'asos_recent' do

  def asos_endpoint_missing?(output)
    output.include?("Our server couldn't find") &&
      output.include?('/asos/recent')
  end

  it 'prints recent observations for a US ICAO station' do
    output = run('asos_recent', 'KDWH')
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(output).not_to include('Traceback')
    expect(output).to include('ASOS observations for')
    expect(output).to include('observation(s)')
    expect(output).to match(/^Time\s+Temp \(C\)\s+Dewpt \(C\)\s+P \(hPa\)\s+U \(m\/s\)\s+V \(m\/s\)\s+Precip \(mm\)\s*$/)
  end

  it 'accepts a 3-letter FAA code for a US airport' do
    output = run('asos_recent', 'DWH')
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(output).not_to include('Traceback')
    expect(output).to include('ASOS observations for')
  end

  it 'accepts a 4-letter international ICAO code' do
    output = run('asos_recent', 'EGLL')
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(output).not_to include('Traceback')
    expect(output).to include('ASOS observations for')
  end

  it 'saves observations to a JSON file' do
    output_path = 'spec_outputs/asos_recent_kdwh.json'
    File.delete(output_path) if File.exist?(output_path)

    output = run('asos_recent', 'KDWH', output_path)
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(output).not_to include('Traceback')
    expect(File.exist?(output_path)).to be true

    body = JSON.parse(File.read(output_path))
    expect(body).to be_a(Hash)
    expect(body).to have_key('station')
    expect(body).to have_key('observations')
    expect(body['observations']).to be_a(Array)
    expect(body['observations'].size).to be > 0

    first = body['observations'].first
    expect(first).to have_key('time')
    expect(first.keys).to include(*%w[temperature_2m dewpoint_2m pressure_msl wind_u_10m wind_v_10m])
  end

  it 'saves observations to a CSV file' do
    require 'csv'

    output_path = 'spec_outputs/asos_recent_kdwh.csv'
    File.delete(output_path) if File.exist?(output_path)

    output = run('asos_recent', 'KDWH', output_path)
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(File.exist?(output_path)).to be true

    rows = CSV.read(output_path)
    expect(rows.size).to be > 1
    expect(rows.first).to include('time', 'temperature_2m', 'dewpoint_2m', 'pressure_msl', 'wind_u_10m', 'wind_v_10m')
  end

  it 'honors --hours to shorten the lookback window' do
    short_path = 'spec_outputs/asos_recent_kdwh_2h.json'
    long_path  = 'spec_outputs/asos_recent_kdwh_48h.json'
    [short_path, long_path].each { |p| File.delete(p) if File.exist?(p) }

    short_output = run('asos_recent', 'KDWH', '-H', '2', short_path)
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(short_output)

    long_output = run('asos_recent', 'KDWH', '-H', '48', long_path)
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(long_output)

    short_body = JSON.parse(File.read(short_path))
    long_body  = JSON.parse(File.read(long_path))

    expect(short_body['observations'].size).to be > 0
    expect(long_body['observations'].size).to be > 0
    expect(long_body['observations'].size).to be >= short_body['observations'].size
  end

  it 'honors --since with an ISO 8601 timestamp' do
    output_path = 'spec_outputs/asos_recent_kdwh_since.json'
    File.delete(output_path) if File.exist?(output_path)

    # 12 hours ago in ISO 8601
    since = (Time.now.utc - 12 * 3600).strftime('%Y-%m-%dT%H:%M:%SZ')
    output = run('asos_recent', 'KDWH', '-s', since, output_path)
    skip 'asos/recent endpoint is not deployed yet' if asos_endpoint_missing?(output)

    expect(File.exist?(output_path)).to be true
    body = JSON.parse(File.read(output_path))
    expect(body['observations']).to be_a(Array)

    cutoff = Time.parse(since)
    body['observations'].each do |obs|
      next unless obs['time']
      expect(Time.parse(obs['time'])).to be >= cutoff
    end
  end

  it 'errors usefully when no station is provided' do
    output = run('asos_recent')
    # argparse complains and exits non-zero before we touch the network
    expect(output).to include('the following arguments are required: station')
  end
end
