# dust-filter
dust filter RPi code

# deps
  - python3-yaml
  - python3-flask
  - python3-matplotlib

# test
make test

# run on real hardware (sensors and relays) locally
nohup python3 -m dust_filter.core &
