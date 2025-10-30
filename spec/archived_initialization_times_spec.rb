describe 'archived_init_times' do
  it 'gets a list of archived initialization times' do
    output = run('archived_init_times')
    expect(output).to include('Available archived initialization times:')
    expect(output.split("\n").size).to be > 2
  end

  it 'gets a list of archived initialization times with an ensemble member' do
    output = run('archived_init_times', '--model', 'wm4-ens', '--ens-member', '1')
    expect(output).to include('Available archived initialization times:')
    expect(output.split("\n").size).to be > 2
  end

  it 'gets a list of archived initialization times with intracycle model' do
    output = run('archived_init_times', '--model', 'wm4-intra')
    expect(output).to include('Available archived initialization times:')
    expect(output.split("\n").size).to be > 2
  end

  it 'gets archived initialization times with a page_end parameter' do
    output = run('archived_init_times', '--model', 'wm4', '--page-end', '2025-09-30T00:00:00Z')
    expect(output).to include('Available archived initialization times:')
    expect(output.split("\n").size).to be >= 1

    # verify that all initialization times are before 2025-09-30T00:00:00Z
    output.split("\n").each do |line|
      next unless line.start_with?(' - ')

      # eg " - 2025-02-01T00:00:00.000Z"
      expect(line).to match(/^ - \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/)
      expect(Time.parse(line.split(' ').last)).to be <= Time.parse('2025-09-30T00:00:00Z')
    end
  end
end


