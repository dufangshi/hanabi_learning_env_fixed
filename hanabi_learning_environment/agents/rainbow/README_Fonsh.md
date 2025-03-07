## to train the model:
```
python -um train --base_dir=./tmp/hanabi_rainbow                  --checkpoint_dir=./tmp/hanabi_rainbow/checkpoints                  --logging_dir=./tmp/hanabi_rainbow/logs                  --gin_files=./configs/hanabi_rainbow.gin
```

make sure to create tmp/checkpoints, and tmp/logs 


## to run the model. create pretrained_model under rainbow, and then put checkpoints inside, then
```
hanabi-learning-environment/hanabi_learning_environment/agents/rainbow$ python create_rainbow_data.py --num_games 10 --savedir ../replay_data/

# or use
hanabi-learning-environment/examples$ python rl_env_example.py 

```
