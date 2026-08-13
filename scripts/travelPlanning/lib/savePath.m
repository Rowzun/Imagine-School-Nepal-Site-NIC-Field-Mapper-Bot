function savePath(traj, filename, format)
% SAVEPATH  Write an N×3 trajectory to disk, CSV or space-delimited ASCII.
%
%   savePath(traj,'file.csv','csv')      % comma-separated
%   savePath(traj,'file.txt','ascii')    % space-separated
%
%   Always uses 6-decimal precision.  Falls back to DLMWRITE on
%   older MATLAB versions that lack the 'Precision' option for WRITEMATRIX.

% --- basic checks --------------------------------------------------------
if nargin~=3
    error('savePath needs three inputs: traj, filename, format');
end
if ~ismatrix(traj) || size(traj,2)~=3
    error('traj must be an N×3 numeric array');
end
format = lower(char(format));
if ~ismember(format,{'csv','ascii'})
    error('format must be ''csv'' or ''ascii''');
end

% --- delimiter -----------------------------------------------------------
if strcmp(format,'csv')
    delim = ',';
else
    delim = ' ';
end

% --- write file ----------------------------------------------------------
try
    % R2022a+ supports the Precision option
    writematrix(traj, filename, ...
                'Delimiter', delim, ...
                'Precision',  '%.6f');
catch
    % Fallback for older MATLAB releases
    dlmwrite(filename, traj, ...
             'delimiter', delim, ...
             'precision', '%.6f');
end

fprintf('Path saved to %s  (%s)\n', filename, format);
end
