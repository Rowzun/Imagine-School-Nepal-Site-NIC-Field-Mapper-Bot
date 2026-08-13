function path = scanTrajectory(scanMask, xC, yC, zC, algo)
% SCANTRAJECTORY  Convert a logical voxel mask into an ordered path.
%
%   path = SCANTRAJECTORY(scanMask, xC, yC, zC, algo)
%
%   Inputs
%   ------
%   scanMask : logical ny × nx × nz   – TRUE voxels to cover
%   xC,yC,zC : voxel-centre vectors   – same ones used in physicalDomain
%   algo     : 'boustrophedon' | 'greedy' | 'tsp' | 'layerwise'
%              (default = 'boustrophedon')
%
%   Output
%   -------
%   path     : N × 3 double array – ordered coordinates of visited voxels
%   ----------------------------------------------------------------------

    if nargin < 5 || isempty(algo),  algo = 'boustrophedon';  end
    algo = lower(algo);

    % ----- pull out centre coordinates of ALL TRUE voxels ----------------
    [Yidx,Xidx,Zidx] = ind2sub(size(scanMask), find(scanMask));
    pts = [xC(Xidx).', yC(Yidx).', zC(Zidx).'];      % N × 3

    if isempty(pts)
        path = zeros(0,3);   return
    end

    switch algo
    %----------------------------------------------------------------------
    case 'boustrophedon'
        path = boustrophedon(scanMask,xC,yC,zC);

    %----------------------------------------------------------------------
    case 'greedy'
        path = greedyPath(pts);

    %----------------------------------------------------------------------
    case 'tsp'
        path = greedyPath(pts);          % 1) seed with greedy
        path = twoOpt(path);             % 2) improve with 2-opt

    %----------------------------------------------------------------------
        
    case 'raw'
    % MEMORY-ORDER baseline:  Y fastest, then X, then Z  (as stored by meshgrid)
    % No optimisation whatsoever.
    [~,sortIdx] = sortrows([Yidx Xidx Zidx]);   % row-major
    path = pts(sortIdx,:);                      % but pts already in that order!

    %----------------------------------------------------------------------
    case 'layerwise'
        % Build greedy sub-paths layer by layer
        zLayers = sort(unique(pts(:,3)));   path = [];
        lastPt  = [min(xC) min(yC) min(zC)];  % start origin
        for zl = zLayers.'
            slicePts = pts( abs(pts(:,3)-zl) < 1e-12 , : );
            if isempty(slicePts),  continue,  end

            % start the slice at whichever voxel is nearest to lastPt
            d = pdist2(lastPt,slicePts); [~,idxStart] = min(d);
            sliceOrder = greedyPath(slicePts, idxStart);
            path  = [path; sliceOrder];
            lastPt = sliceOrder(end,:);
        end

    otherwise
        error('Unknown trajectory algorithm "%s".',algo);
    end
end
% ========================================================================
function path = boustrophedon(mask,xC,yC,zC)
    [ny,nx,nz] = size(mask);
    path = [];

    flipNextRow = false;
    for iz = 1:nz
        layer = mask(:,:,iz);                % Y,X layout
        if ~any(layer,'all'), continue, end

        rows = find(any(layer,2));           % Y indices containing voxels
        for k = 1:numel(rows)
            iy = rows(k);
            xs = find(layer(iy,:));          % X indices in this row
            if isempty(xs), continue, end
            if xor(mod(k-1,2)==1, flipNextRow)
                xs = fliplr(xs);
            end
            y  = yC(iy);  z = zC(iz);
            path = [path; [xC(xs).', y*ones(numel(xs),1), z*ones(numel(xs),1)]];
        end
        lastX = path(end,1);
        flipNextRow = lastX > mean(xC);
    end
end
% ========================================================================
function path = greedyPath(pts, startIdx)
    % pts : N×3
    if nargin<2  % start at minimal x,y,z voxel
        [~,startIdx] = min( pts(:,1)*1e6 + pts(:,2)*1e3 + pts(:,3) );
    end
    N = size(pts,1);
    visited = false(N,1);
    path    = zeros(N,3);

    idx = startIdx;
    for k = 1:N
        path(k,:)   = pts(idx,:);
        visited(idx)= true;

        % pick next unvisited nearest neighbour
        if k<N
            remainingIdx = find(~visited);
            d = pdist2(path(k,:), pts(remainingIdx,:));
            [~,minJ] = min(d);
            idx = remainingIdx(minJ);
        end
    end
end
% ========================================================================
function path = twoOpt(path)
    % Simple 2-opt improvement (swap edges if total length shortens)
    improved = true;  N = size(path,1);
    while improved
        improved = false;
        for i = 2:N-2
            for j = i+1:N-1
                % edges (i-1,i) and (j,j+1) → (i-1,j) + (i,j+1)?
                a = path(i-1,:); b = path(i,:);
                c = path(j,:);   d = path(j+1,:);
                old = norm(a-b)+norm(c-d);
                new = norm(a-c)+norm(b-d);
                if new < old
                    path(i:j,:) = flipud(path(i:j,:)); 
                    improved = true;
                end
            end
        end
    end
end
