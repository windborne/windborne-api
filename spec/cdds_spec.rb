describe 'cdds' do
  def latest_init_time_for(model)
    output = run('init_times', '--model', model)
    line = output.split("\n").find { |l| l.start_with?('Latest initialization time:') }
    line.split(': ', 2)[1]
  end

  it 'prints CDDs to stdout' do
    init_time = latest_init_time_for('wm4')
    output = run('cdds', init_time, '--model', 'wm4')
    # Expect at least one region header and a date line with a value
    expect(output.split("\n").size).to be > 10
    expect(output).to match(/\n[A-Za-z].+:\n/)
    expect(output).to match(/\n\s{2}\d{4}-\d{2}-\d{2}:\s*[-+]?\d/)
    expect(output.downcase).not_to include('traceback')
  end

  it 'saves CDDs to CSV' do
    require 'csv'
    init_time = latest_init_time_for('wm4')
    path = 'spec_outputs/cdd.csv'
    File.delete(path) if File.exist?(path)

    run('cdds', init_time, '--model', 'wm4', '-o', path)

    expect(File.exist?(path)).to be true
    csv = CSV.read(path, headers: true)
    expect(csv.headers.first).to eq('Region')
    expect(csv.size).to be > 10
    csv.each do |row|
      values = row.to_h.values[1..]
      expect(values.any? { |v| v && v.strip != '' }).to be true
    end
  end
end


