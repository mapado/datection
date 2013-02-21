Datection provides you with a parser that can extract and normalize
date/time related expressions.

For example, the french expression "le lundi 15 mars, de 15h30 à 16h"
will be normalized into the following JSON structure:

{
    'date':
    {
        'day': 15,
        'month': 3,
        'year': None
    },
    'time':
    {
        'end_time':
        {
            'hour': 16,
            'minute': 0
        },
        'start_time':
        {
            'hour': 15,
            'minute': 30
        }
    }
}

No external dependencies are needed.