# Project Less

# Results

## Example:

> Query:
> In the file 'edit_distance/edit_distance.py', there is function called '`lowest_...`'. Edit the function by using better names #for the variables. Do not rename the function"

**Old Code**:

```python
# ...
def lowest_cost_action(ic, dc, sc, im, dm, sm, cost) -> str:
    """Given the following values, choose the action (insertion, deletion,
    or substitution), that results in the lowest cost (ties are broken using
    the 'match' score).  This is used within the dynamic programming algorithm.

    * ic - insertion cost

    * dc - deletion cost

    * sc - substitution cost

    * im - insertion match (score)

    * dm - deletion match (score)

    * sm - substitution match (score)
    """
    best_action = None
    best_match_count = -1
    min_cost = min(ic, dc, sc)
    if min_cost == sc and cost == 0:
        best_action = EQUAL
        best_match_count = sm
    elif min_cost == sc and cost == 1:
        best_action = REPLACE
        best_match_count = sm
    elif min_cost == ic and im > best_match_count:
        best_action = INSERT
        best_match_count = im
    elif min_cost == dc and dm > best_match_count:
        best_action = DELETE
        best_match_count = dm
    else:
        raise Exception("internal error: invalid lowest cost action")
    return best_action
```

**New Code**

```python
#...
def lowest_cost_action(insertion_cost, deletion_cost, substitution_cost, insertion_match, deletion_match, substitution_match, cost) -> str:
    """Given the following values, choose the action (insertion, deletion,
    or substitution), that results in the lowest cost (ties are broken using
    the 'match' score).  This is used within the dynamic programming algorithm.

    * insertion_cost - insertion cost

    * deletion_cost - deletion cost

    * substitution_cost - substitution cost

    * insertion_match - insertion match (score)

    * deletion_match - deletion match (score)

    * substitution_match - substitution match (score)
    """
    best_action = None
    best_match_count = -1
    min_cost = min(insertion_cost, deletion_cost, substitution_cost)
    if min_cost == substitution_cost and cost == 0:
        best_action = EQUAL
        best_match_count = substitution_match
    elif min_cost == substitution_cost and cost == 1:
        best_action = REPLACE
        best_match_count = substitution_match
    elif min_cost == insertion_cost and insertion_match > best_match_count:
        best_action = INSERT
        best_match_count = insertion_match
    elif min_cost == deletion_cost and deletion_match > best_match_count:
        best_action = DELETE
        best_match_count = deletion_match
    else:
        raise Exception("internal error: invalid lowest cost action")
    return best_action

```

Git Diff:
![Photo](pics/git%20diff.PNG)

State and History of Agent:
![Photo](pics/Less%20Code%20Example.PNG)

# Running

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

    ```bash
    python cli.py <query> --repo <path to repo you want to execute agent on>
    ```

# Development

### VSCode Plugins

- Python
- Black Formatter
- Python Environment Manager
- Python Docstring Generator
- Pylint
