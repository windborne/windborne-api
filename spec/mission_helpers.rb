def sample_mission_id

  cache_path = 'spec_outputs/_tmp_sample_mission.json'
  if File.exist?(cache_path)
    cache_data = JSON.parse(File.read(cache_path))
    written_at = cache_data['written_at']
    seconds_since_fetch = Time.now.to_i - written_at.to_i
    return cache_data['id'] if seconds_since_fetch < 60
  end

  missions_path = 'spec_outputs/_tmp_missions.json'

  # run if it's been more than a minute since the last time we ran it
  run('flying-missions', missions_path)
  
  return nil unless File.exist?(missions_path)
  body = JSON.parse(File.read(missions_path))
  missions = body['missions'] || []
  ids = missions.map { |m| m['id'] }.compact
  sample_mission_id = ids.last

  # write to cache
  File.write(cache_path, JSON.dump({ 
    'id' => sample_mission_id, 
    'written_at' => Time.now.to_i 
  }))

  sample_mission_id
end