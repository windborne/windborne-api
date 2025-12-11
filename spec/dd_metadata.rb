describe 'cdds' do
  def latest_init_time_for(model)
    output = run('init_times', '--model', model)
    line = output.split("\n").find { |l| l.start_with?('Latest initialization time:') }
    line.split(': ', 2)[1]
  end

  it 'prints created_at to stdout' do
    init_time = latest_init_time_for('wm4')
    output = run('dd_metadata', init_time, '--model', 'wm4')
    # Expect at least one region header and a date line with a value
    expect(output.split("\n").size).to be == 1
    expect(output).to match(/Created at \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/)
    expect(output.downcase).not_to include('traceback')
  end
end


