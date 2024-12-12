To setup the graphing install run the following command

```
pip install plotly.express pandas
```

After that you can just run ttlens reguarly and use the graph command like this

```
graph power
```

You can also save to csv

```
graph current --save-csv=log.csv
```

Or load from csv

```
graph current --from-csv=log.csv
```

You can also specify the size 

```
graph current --size 40000
```

You can graph everything with
```
graph all
```

When you run the grpah command, a localhost server will be hosted and you can just click on the link from the terminal to see the graph