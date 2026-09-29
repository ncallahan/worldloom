# Experiment Conventions

Experiments are evidence about the architecture or a model, not architecture by themselves.

Each substantial experiment should record:

- purpose and question
- model implementation/version
- configuration
- random seed(s)
- software/environment versions
- execution parameters
- measurements
- output locations
- interpretation, kept distinct from raw results

A suggested layout is:

    experiments/<id>/
      README.md
      config.yaml
      run.py
      results/

Experiments should be reproducible where practical and should not overwrite raw outputs without recording the change.
