describe 'auth' do

  it 'requests keys if none are set' do
    output = run('observations-page', "2024-12-01_06:00", wb_client_id: '', wb_api_key: '')
    expect(output).to include('set your Client ID and API key by setting the environment variables WB_CLIENT_ID and WB_API_KEY')
  end

  it 'accepts global keys' do
    output = run('observations-page', "2024-12-01_06:00", wb_client_id: 'global')
    expect(output).to start_with('{')
    details = JSON.parse(output)
    expect(details['observations'].size).to be > 0
  end

  it 'rejects user keys' do
    output = run('observations-page', "2024-12-01_06:00", wb_client_id: 'user')
    expect(output).to start_with('{')
    details = JSON.parse(output)
    expect(details['observations'].size).to eq(0)
  end

end
