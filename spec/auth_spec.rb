require 'base64'
require 'json'

describe 'auth' do
  def combined_api_key_for(name, padded: true)
    credentials = JSON.parse(File.read(__dir__ + '/credentials.json'))
    combined_key = "wb_#{Base64.strict_encode64("#{credentials["#{name}_client_id"]}:#{credentials["#{name}_api_key"]}")}"
    padded ? combined_key : combined_key.delete_suffix('=')
  end

  def init_times_output_for(**kwargs)
    run('init-times', **kwargs)
  end

  it 'requests keys if none are set' do
    output = run('observations-page', "2024-12-01_06:00", wb_client_id: '', wb_api_key: '')
    expect(output).to include('set the environment variable WB_API_KEY')
  end

  it 'accepts global keys' do
    output = init_times_output_for(wb_client_id: 'global')
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
  end

  it 'accepts user keys for init times' do
    output = init_times_output_for(wb_client_id: 'user')
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
  end

  it 'accepts combined global keys' do
    output = init_times_output_for(wb_client_id: nil, wb_api_key: combined_api_key_for('global'))
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
  end

  it 'accepts unpadded combined global keys' do
    output = init_times_output_for(wb_client_id: nil, wb_api_key: combined_api_key_for('global', padded: false))
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
  end

  it 'rejects malformed combined keys' do
    output = init_times_output_for(wb_client_id: nil, wb_api_key: 'wb_not-base64')
    expect(output).to include("Your WB_API_KEY doesn't look valid")
  end

end
