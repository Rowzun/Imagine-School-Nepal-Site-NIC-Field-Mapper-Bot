function d = travelDistance(path)
% TRAVELDISTANCE  Total Euclidean length of a voxel-to-voxel trajectory.
%
%   d = travelDistance(path)
%
%   path : N×3 numeric array whose rows are successive (x,y,z) points.
%   d    : scalar, sum of Euclidean distances between consecutive points.
%
%   Example
%   -------
%     d = travelDistance(myPath);
%     fprintf('Total travel = %.2f mm\n', d);

    if size(path,2) ~= 3
        error('Input PATH must be an N×3 array of (x,y,z) coordinates.');
    end
    diffs = diff(path, 1, 1);          % (N-1)×3
    d     = sum( sqrt( sum(diffs.^2, 2 ) ) );
end